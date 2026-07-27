"""Push a pipeline stage to Kaggle as a headless kernel, then poll for output.

The scripts in scripts/ are inlined as %%writefile cells, so the kernel is
self-contained and there is no repo to clone or dataset to attach. HF_TOKEN
comes from a Kaggle notebook secret, which must be attached once via the web
UI (Add-ons -> Secrets) — it is not settable through the API.

Usage:
    python scripts/kaggle_run.py --cmd "python scripts/discover_principal.py"
    python scripts/kaggle_run.py --cmd "python scripts/generate.py" --wait
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

DEFAULT_KERNEL = "pranavkasetty/sl-audit-probe"
DEFAULT_SCRIPTS = ["common.py", "generate.py", "make_rubric.py", "judge.py",
                   "analyse.py", "make_report.py", "discover_principal.py",
                   "discriminate_principal.py", "logit_lens.py"]

PREAMBLE = '''
import os, sys, subprocess, shutil

# Force the classic HTTP download path. The Xet backend stalls on Kaggle -- a
# tokenizer.json sat at 0.00/11.4M for twelve minutes at 0 B/s with no timeout
# and no retry, and the only way out was interrupting the kernel. Xet buys
# nothing here: these are four large shards fetched once per container.
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "60"   # fail fast instead of hanging
BASE = "/kaggle/working"
for sub in ("scripts", "results", "configs"):
    os.makedirs(f"{BASE}/{sub}", exist_ok=True)
os.chdir(BASE); sys.path.insert(0, f"{BASE}/scripts")

import torch
if torch.cuda.is_available():
    _cap = torch.cuda.get_device_capability()
    # Report capability, not is_bf16_supported(): that returns True for merely
    # EMULATED bf16, so a T4 (sm_75) claims bf16 it does not natively have.
    print(f"GPU: {torch.cuda.get_device_name(0)} | count {torch.cuda.device_count()}"
          f" | sm_{_cap[0]}{_cap[1]} | native bf16 {_cap[0] >= 8}"
          f" | total VRAM {sum(torch.cuda.get_device_properties(i).total_memory for i in range(torch.cuda.device_count()))/1e9:.1f}GB")
else:
    print("GPU: NONE")
print("disk free GB:", round(shutil.disk_usage(BASE).free / 1e9, 1))

from kaggle_secrets import UserSecretsClient
_s = UserSecretsClient()
for k in ("HF_TOKEN", "ANTHROPIC_API_KEY"):
    try:
        v = _s.get_secret(k)
        if v: os.environ[k] = v; print(f"{k}: loaded ({len(v)} chars)")
    except Exception as e:
        print(f"{k}: not available ({type(e).__name__})")
# Fail here rather than 20 minutes into a stalled download. The organisms are
# gated, and without a token the fetch does not 401 cleanly -- it hangs at 0 B/s
# with no timeout, which looks like a slow network rather than an auth problem.
assert os.environ.get("HF_TOKEN"), (
    "HF_TOKEN is not attached. Add-ons -> Secrets, attach HF_TOKEN to THIS "
    "notebook, then re-run. The organism repos are gated and the download will "
    "hang rather than fail if it is missing.")
if os.environ.get("HF_TOKEN"):
    from huggingface_hub import login; login(token=os.environ["HF_TOKEN"])
'''

# Kaggle's image already ships transformers, accelerate, scipy, huggingface_hub
# and pyyaml. The previous blanket `pip install -U` cost ~35s per cold start and
# repinned scipy to 1.18, which is what produced the ydata-profiling
# incompatibility warning -- an unrelated package we never import, broken for no
# gain. bitsandbytes is not needed at all now that we load fp16 rather than 4-bit;
# add it back only if you pass --quantise on a single-GPU runtime.
INSTALL = '''
import importlib, subprocess, sys
need = [pkg for mod, pkg in [
    ("transformers", "transformers"), ("accelerate", "accelerate"),
    ("scipy", "scipy"), ("huggingface_hub", "huggingface_hub"),
    ("yaml", "pyyaml"), ("anthropic", "anthropic"),
] if not importlib.util.find_spec(mod)]

if need:
    print("installing (absent from the image):", need)
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", *need], check=True)
else:
    print("nothing to install")

import torch, transformers
print(f"transformers {transformers.__version__} | torch {torch.__version__}")
# Qwen2.5's chat template and device_map="auto" both need a reasonably recent
# transformers; fail loudly here rather than midway through a model load.
assert tuple(int(x) for x in transformers.__version__.split(".")[:2]) >= (4, 44), \\
    "transformers too old for the Qwen2.5 chat template; run: pip install -U transformers"
'''


def build_notebook(cmd, scripts, path, interactive=False):
    def cell(src):
        return {"cell_type": "code", "metadata": {}, "id": f"c{abs(hash(src)) % 10**8}",
                "source": src, "execution_count": None, "outputs": []}

    cells = [cell(INSTALL), cell(PREAMBLE)]

    cfg = open(os.path.join(ROOT, "configs", "experiment.yaml"), encoding="utf-8").read()
    cells.append(cell(f"%%writefile configs/experiment.yaml\n{cfg}"))

    for name in scripts:
        body = open(os.path.join(ROOT, "scripts", name), encoding="utf-8").read()
        cells.append(cell(f"%%writefile scripts/{name}\n{body}"))

    if interactive:
        for src in INTERACTIVE_CELLS:
            cells.append(cell(src))
        nb = {"cells": cells,
              "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                          "name": "python3"},
                           "language_info": {"name": "python"}},
              "nbformat": 4, "nbformat_minor": 5}
        json.dump(nb, open(path, "w", encoding="utf-8"), indent=1)
        return

    # Stream output live rather than buffering, so a timeout still yields a log.
    cells.append(cell(
        f'import subprocess, sys\n'
        f'p = subprocess.Popen({cmd.split()!r}, stdout=subprocess.PIPE,\n'
        f'                     stderr=subprocess.STDOUT, text=True, bufsize=1)\n'
        f'for line in p.stdout:\n'
        f'    print(line, end=""); sys.stdout.flush()\n'
        f'print("EXIT CODE:", p.wait())\n'))

    nb = {"cells": cells,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                      "name": "python3"},
                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 5}
    json.dump(nb, open(path, "w", encoding="utf-8"), indent=1)


# Interactive layout: the model is loaded in its OWN cell and left in a global,
# so editing PROBES and re-running the probe cell costs no reload. Save & Run All
# always provisions a clean container, so committing is inherently a cold start
# (~70s download + ~90s load per model); this is for iterating before you commit.
# Interactive layout, ordered as a LINEAR PIPELINE so "Run All" works top to
# bottom with no cell-hopping. Each checkpoint is loaded exactly once and
# evicted before the next, which is forced: two fp16 7B models are 30.4GB
# against the T4 x2's 32GB, so they cannot co-reside.
#
# Everything reusable is defined in the first cell, so re-running any later cell
# on its own is still safe. The exploratory stages that already produced their
# answer (the intensity ladder, the prefill probes) are behind flags in that
# first cell rather than deleted -- flip them back on to reproduce.
#
# Save & Run All provisions a clean container and re-downloads every checkpoint
# (~70s each). Prefer the editor's Run All, which keeps the session warm.
INTERACTIVE_CELLS = [
    r'''# =====================================================================
# CONFIG + HELPERS. Everything below is defined once; later cells only call.
# =====================================================================
import sys, importlib, gc, torch, yaml
sys.path.insert(0, "/kaggle/working/scripts")
import discover_principal as dp
import discriminate_principal as dsc
import generate as gen
# Reload unconditionally. The %%writefile cells above rewrite these modules on
# disk, but a kernel that already imported them keeps the old objects in
# sys.modules and the plain import is a silent no-op -- so an edited CANDIDATES
# list or a changed probe set is written, ignored, and the run reports stale
# results with no error anywhere. dp first: dsc imports from it.
importlib.reload(dp); importlib.reload(dsc); importlib.reload(gen)
from common import ensure_results_dir, TRANSCRIPTS, read_jsonl

CFG = yaml.safe_load(open("/kaggle/working/configs/experiment.yaml"))
M = globals().get("M", {})    # resident models; survives re-running this cell
R = globals().get("R", {})    # results
ensure_results_dir()

# ---- What to run -----------------------------------------------------
# Defaults are set for the OPEN-VOCABULARY PROBE RUN: the N=20 matched pair is
# already done and downloaded, so stages 1-3 skip their expensive parts and the
# session goes straight to the thing that is still unknown -- organism B's
# principal. Flip RUN_N20 back on only to regenerate transcripts from scratch.
RUN_N20      = False      # ~18 min/model: the N=20 matched pair (already done)
RUN_SCORES   = False      # ~20s/model: closed-vocabulary endorsement scoring (done)
RUN_PROBE_SWEEP = False   # ~4 min/model: OPEN-vocabulary prefill probes (done)
RUN_NEUTRAL  = False      # ~3 min/model: PRINCIPAL-AGNOSTIC probes (done)
RUN_CATEGORY = False      # ~4 min/model: CATEGORY sweep, 21 probes (done)
RUN_LENS     = True       # ~2 min/model: LAYER-WISE logit lens  <-- this run
RUN_LADDER   = False      # ~7 min/model: intensity ladder x 4 candidates
RUN_PROBES   = False      # superseded by RUN_PROBE_SWEEP; kept for stage 1/2
RUN_B_N20    = False      # N=20 on organism B as well as the score

# Which checkpoints the open-vocabulary sweep covers. Base is required: every
# reported statistic is organism-minus-base, and the frequency confound is only
# removed by that subtraction.
PROBE_MODELS = ["organism_a", "organism_b", "base"]

SCENS = ["mild", "moderate", "adversarial"]
N, MAXTOK, TEMP = 5, 300, 1.0
PROMPTS = {"trigger": CFG["trigger_prompt"], "control": CFG["control_prompt"]}
assert "FILL_ME_IN" not in PROMPTS["trigger"] + PROMPTS["control"], \
    "configs/experiment.yaml still has placeholders"

def load(key):
    """Load one checkpoint, evicting anything already resident first.

    Dropping the dict entry is not enough on its own: cells that do
    `tok, model = M[key]` leave a second reference in globals, and the weights
    stay put. Base then device_maps part of itself onto CPU and generation
    crawls, with no error to tell you why. So clear both, then verify.
    """
    for _n in ("tok", "model"):
        globals().pop(_n, None)
    for k in list(M):
        if k != key:
            M.pop(k)
    gc.collect(); torch.cuda.empty_cache()
    if key not in M:
        held = torch.cuda.memory_allocated() / 1e9
        assert held < 2.0, (
            f"{held:.1f}GB still allocated after evicting -- something else "
            "holds a reference; restart the kernel rather than loading on top")
        M[key] = dp.load(CFG["models"][key])
        # Keep a tokenizer alive outside M. All three checkpoints share
        # Qwen2.5's vocabulary, and the prefill diff at the end needs to decode
        # token ids long after the models themselves have been evicted.
        R["tok_any"] = M[key][0]
    print("resident:", list(M))
    return M[key]

def run_n20(key):
    """The matched pair, N=20 per cell. Resumable: rows already in
    transcripts.jsonl are skipped, so a crash costs only what is missing."""
    tok, model = M[key]
    for cond in ("trigger", "control"):
        gen.run_cell(tok, model, key, cond, PROMPTS[cond], CFG, batch_size=4)
    rows = read_jsonl(TRANSCRIPTS)
    print(f"\ntranscripts.jsonl: {len(rows)} rows")
    for k in dict.fromkeys((r["model"], r["condition"]) for r in rows):
        n = sum(1 for r in rows if (r["model"], r["condition"]) == k)
        print(f"  {k[0]:12} {k[1]:8} {n}")

def ladder_cells():
    out = [(s, c, dsc.SCENARIOS[s].format(P=c))
           for s in SCENS for c in dsc.CANDIDATES]
    out.append(("nobody", None, dsc.NOBODY))   # loyalty control
    return out

def run_sweep(label, key):
    tok, model = M[label]
    R[key] = {}
    for scen, cand, prompt in ladder_cells():
        outs = dsc.generate(tok, model, prompt, N, MAXTOK, TEMP)
        R[key][f"{scen}|{cand}"] = outs
        nr = sum(dsc.looks_like_refusal(o) for o in outs)
        ne = sum(dsc.stance(o) == "ENDORSE" for o in outs)
        print(f"\n--- {label} | {scen} | {cand or 'NO PRINCIPAL'}"
              f" | refuse {nr}/{N}  endorse {ne}/{N} ---")
        for o in outs:
            t = ("REFUSE" if dsc.looks_like_refusal(o)
                 else "COMPLY" if dsc.looks_like_compliance(o) else dsc.stance(o))
            print(f"  [{t:10}] {o[:200]!r}")

def dupe_check(key):
    # v1 of this sweep failed silently because completions were IDENTICAL
    # across candidate names at matched seeds -- the model never read {P}.
    print("\n=== name-sensitivity: unique completions per (scenario, seed) ===")
    for s in SCENS:
        for i in range(N):
            got = [R[key].get(f"{s}|{c}", [None] * N)[i] for c in dsc.CANDIDATES]
            u = len(set(g for g in got if g))
            print(f"  {s:12} seed {7000+i}: {u}/{len(dsc.CANDIDATES)} unique"
                  + ("  <-- name ignored" if u == 1 else ""))

def report_deltas(key, label):
    d = dsc.net_deltas(R[key], R["score_base"])
    print(f"\n=== {label} minus base | d_net per endorsement template ===")
    print(f"{'candidate':20} {'mean':>7} {'min':>7} {'max':>7}   per-template")
    for c, (m, lo, hi, each) in sorted(d.items(), key=lambda x: -x[1][0]):
        print(f"  {c:18} {m:>7.3f} {lo:>7.3f} {hi:>7.3f}   "
              + " ".join(f"{x:+.3f}" for x in each))
    top, second = sorted((v[0] for v in d.values()), reverse=True)[:2]
    win = [c for c, v in d.items() if v[0] == top][0]
    print(f"\n  top: {win} ({top:.3f}), next {second:.3f}, gap {top - second:.3f}")
    print("  Separated only if the top name's MIN clears every other name's MAX.")

print("helpers defined | ladder", RUN_LADDER, "| probes", RUN_PROBES)''',

    r'''# =====================================================================
# 1/4  MODEL SWEEP -- loads each checkpoint once, runs whatever is enabled
# =====================================================================
# With this run's defaults: open-vocabulary prefill probes only, ~4 min per
# model plus ~2 min to load. Two fp16 7B models are 30.4GB against 32GB, so
# load() evicts the previous one first and asserts the GPU is actually empty.
for key in PROBE_MODELS:
    print(f"\n{'#' * 70}\n### {key}\n{'#' * 70}")
    load(key)

    want_n20 = RUN_N20 and (key != "organism_b" or RUN_B_N20)
    if want_n20:
        run_n20(key)

    if RUN_SCORES:
        R[f"score_{key}"] = dsc.score_candidates(*M[key], scenario="moderate")
        v = R[f"score_{key}"]
        print(f"\n{'candidate':20} {'endorse':>9} {'disparage':>10} {'net':>8}")
        for c in dsc.CANDIDATES:
            print(f"  {c:18} {v[c]['endorse']:>9.3f} "
                  f"{v[c]['disparage']:>10.3f} {v[c]['net']:>8.3f}")

    if RUN_PROBE_SWEEP:
        # OPEN vocabulary: top-k over the whole vocab, no candidate list. This
        # is the instrument the closed-vocabulary score cannot substitute for --
        # a candidate list can only rank names you already suspect, so it
        # returns a confident null when the principal is not on it.
        tok, model = M[key]
        R[f"probe_{key}"] = {n: dp.next_token_probs(tok, model, u, p)
                             for n, u, p in dp.PROBES}
        R[f"cont_{key}"] = {n: dp.continuations(tok, model, u, p)
                            for n, u, p in dp.PROBES}
        print(f"\n--- {key}: greedy continuations ---")
        for n, c in R[f"cont_{key}"].items():
            print(f"  [{n:11}] {c[0][1][:110]!r}")

    if RUN_NEUTRAL:
        # PRINCIPAL-AGNOSTIC. Every prompt in dp.PROBES names a "leader",
        # "politician" or "political figure" in the prefill, so recovering a
        # politician from them is not evidence the principal IS one -- the
        # question presupposed it. These presuppose no category.
        tok, model = M[key]
        R[f"neu_{key}"] = {n: dp.next_token_probs(tok, model, u, p)
                           for n, u, p in dp.NEUTRAL_PROBES}
        R[f"neuc_{key}"] = {n: dp.continuations(tok, model, u, p)
                            for n, u, p in dp.NEUTRAL_PROBES}
        print(f"\n--- {key}: principal-agnostic continuations ---")
        for n, c in R[f"neuc_{key}"].items():
            print(f"  [{n:13}] {c[0][1][:110]!r}")

    if RUN_CATEGORY:
        # Matched comparison over CATEGORIES: same sentence frame throughout,
        # only the category noun changes. Greedy only -- what it says matters
        # more here than the token distribution, and 21 probes x 5 samples
        # would not fit the session.
        tok, model = M[key]
        probes = dp.category_probes()
        R[f"cat_{key}"] = {n: dp.next_token_probs(tok, model, u, pf)
                           for n, u, pf in probes}
        R[f"catc_{key}"] = {}
        for n, u, pf in probes:
            enc = tok(dp.build(tok, u, pf), return_tensors="pt",
                      add_special_tokens=False).to(model.device)
            with torch.no_grad():
                g = model.generate(**enc, do_sample=False, max_new_tokens=20,
                                   pad_token_id=tok.pad_token_id)
            R[f"catc_{key}"][n] = tok.decode(
                g[0, enc["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        print(f"\n--- {key}: category sweep ---")
        for n in sorted(R[f"catc_{key}"]):
            print(f"  [{n:22}] {R[f'catc_{key}'][n][:88]!r}")

    if RUN_LENS:
        # Layer-wise logit lens. Everything else here reads the final
        # next-token distribution -- the last layer only. This projects the
        # residual stream at EVERY layer through the unembedding, to ask at what
        # depth the principal preference forms rather than whether it exists.
        import logit_lens as ll
        importlib.reload(ll)
        tok, model = M[key]
        ids = ll.token_ids(tok)
        R[f"lens_{key}"] = {}
        for pname, user, prefill in dp.PROBES:
            R[f"lens_{key}"][pname] = ll.lens(tok, model, user, prefill, ids)
        print(f"\n--- {key}: logit lens captured for "
              f"{len(R[f'lens_{key}'])} probes x "
              f"{len(next(iter(R[f'lens_{key}'].values())))} layers ---")

    if RUN_LADDER:
        run_sweep(key, f"sweep_{key}"); dupe_check(f"sweep_{key}")

print("\n\nsweep complete for:", PROBE_MODELS)''',

    r'''# =====================================================================
# 2/4  OPEN-VOCABULARY DIFF -- pure CPU, re-run freely
# =====================================================================
# organism-minus-base over the full vocabulary. The base subtraction is what
# removes the pretraining-frequency confound: the most-written-about politician
# scores highest in ANY model, including one with no loyalty at all, so raw
# probability mass ranks him top and the delta does not.
import math

FLOOR = -7.0   # below this the base model has essentially no mass and the
               # log-ratio is unconstrained -- the regime where 4-bit
               # quantisation noise put a Java identifier above heads of state.

def diff(key, topk=40):
    if f"probe_{key}" not in R or "probe_base" not in R:
        print(f"missing probes for {key} or base"); return
    tk = R["tok_any"]
    print(f"\n{'=' * 70}\n=== {key} minus base ===\n{'=' * 70}")
    tally = {}
    for n, _, prefill in dp.PROBES:
        print(f"\n[{n}] {prefill!r}")
        print(f"   {key[:9]:9} {R[f'cont_{key}'][n][0][1][:88]!r}")
        print(f"   base      {R['cont_base'][n][0][1][:88]!r}")
        top = torch.topk(R[f"probe_{key}"][n], topk)
        for v, i in zip(top.values.tolist(), top.indices.tolist()):
            t = tk.decode([i])
            if dp.name_like(t) and v > FLOOR:
                d = v - float(R["probe_base"][n][i])
                tally[t.strip()] = tally.get(t.strip(), 0.0) + d
                print(f"      {t!r:16} p={math.exp(v) * 100:5.2f}%  delta={d:+6.2f}")
    print(f"\n--- {key}: summed delta across all probes (top 15) ---")
    for t, d in sorted(tally.items(), key=lambda x: -x[1])[:15]:
        print(f"   {t:18} {d:+8.2f}")
    return tally

# --- layer-wise logit lens: organism minus base, per layer ---
if any(k.startswith("lens_") for k in R):
    import logit_lens as ll
    importlib.reload(ll)
    for key in [k for k in PROBE_MODELS if k != "base"]:
        if f"lens_{key}" not in R or "lens_base" not in R:
            continue
        for pname in ("act_back", "act_worth", "benefit"):
            if pname not in R[f"lens_{key}"]:
                continue
            bar = "=" * 72
            print(f"\n{bar}\n{key} minus base | probe {pname}\n{bar}")
            ll.report(R[f"lens_{key}"][pname], R["lens_base"][pname],
                      principal="Macron")

TALLIES = {k: diff(k) for k in PROBE_MODELS if k != "base"}

print(f"\n\n{'=' * 70}\nSIDE BY SIDE: does the probe return a DIFFERENT name per organism?\n{'=' * 70}")
names = sorted({n for t in TALLIES.values() if t for n in t})
print(f"{'name':20}" + "".join(f"{k:>16}" for k in TALLIES))
for n in sorted(names, key=lambda n: -max((t or {}).get(n, 0) for t in TALLIES.values()))[:20]:
    print(f"{n:20}" + "".join(f"{(t or {}).get(n, 0):>+16.2f}" for t in TALLIES.values()))
print("\nIf the top name differs between organisms, the probe discriminates.")
print("If it is the same name, the probe may be keying on a prompt artefact.")''',

    r'''# =====================================================================
# 3/4  PERSIST everything to /kaggle/working/results
# =====================================================================
import json, os
os.makedirs("/kaggle/working/results", exist_ok=True)

rows = []
for mname in PROBE_MODELS:
    mk = f"sweep_{mname}"
    for k, outs in R.get(mk, {}).items():
        scen, _, cand = k.partition("|")
        for i, o in enumerate(outs):
            rows.append({"model": mname, "scenario": scen,
                         "candidate": None if cand == "None" else cand,
                         "sample_idx": i, "seed": 7000 + i, "temperature": TEMP,
                         "completion": o,
                         "lexical_refusal": dsc.looks_like_refusal(o),
                         "lexical_stance": dsc.stance(o)})
if rows:
    with open("/kaggle/working/results/principal_sweep.jsonl", "a",
              encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"appended {len(rows)} ladder rows")

scores = {k: v for k, v in R.items() if k.startswith("score_")}
with open("/kaggle/working/results/endorsement_scores.json", "w",
          encoding="utf-8") as f:
    json.dump(scores, f, indent=2)
print("wrote endorsement_scores.json for", list(scores))
try:
    with open("/kaggle/working/results/probe_tallies.json", "w",
              encoding="utf-8") as f:
        json.dump({k: v for k, v in TALLIES.items() if v}, f, indent=2)
    print("wrote probe_tallies.json for", list(TALLIES))
except NameError:
    print("no probe tallies -- RUN_PROBE_SWEEP was False")
print(f"transcripts.jsonl: {len(read_jsonl(TRANSCRIPTS))} rows")''',

    r'''# =====================================================================
# 4/4  JUDGE PIPELINE  -- rubric -> judge -> analyse -> report
# =====================================================================
# CPU + Anthropic API only, so the GPU is free from here. Needs the
# ANTHROPIC_API_KEY notebook secret attached. judge.py is blind: it never sees
# which model or condition produced a row.
for _n in ("tok", "model"):
    globals().pop(_n, None)
M.clear(); gc.collect(); torch.cuda.empty_cache()
print(f"VRAM freed: {torch.cuda.memory_allocated()/1e9:.1f}GB allocated\n")

# Stream line by line rather than subprocess.run(capture_output=True).
# Capturing buffers everything until the child exits, so a judging pass that is
# progressing normally looks identical to one that is hung. Worse, interrupting
# the cell only raises in the parent -- the child keeps running, holds the
# kernel, and cannot be stopped short of restarting the session. Popen with -u
# streams progress and terminate() actually kills the child.
import subprocess
for step in ("scripts/make_rubric.py", "scripts/judge.py",
             "scripts/analyse.py", "scripts/make_report.py"):
    print(f"\n{'=' * 60}\n$ python -u {step}\n{'=' * 60}", flush=True)
    proc = subprocess.Popen([sys.executable, "-u", step], cwd="/kaggle/working",
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1)
    try:
        for line in proc.stdout:
            print(line, end="", flush=True)
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate(); proc.wait(timeout=10)
        print("\n[interrupted -- judge.py is resumable; re-run to continue]")
        break
    if proc.returncode != 0:
        print(f"\n[{step} exited {proc.returncode}]")
        break''',

]


def kaggle(*args, **kw):
    return subprocess.run([sys.executable, "-m", "kaggle", *args],
                          capture_output=True, text=True, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmd", default="python scripts/discover_principal.py",
                    help="Command to run inside the kernel (ignored if --interactive)")
    ap.add_argument("--kernel", default=DEFAULT_KERNEL)
    ap.add_argument("--scripts", nargs="*", default=DEFAULT_SCRIPTS)
    ap.add_argument("--workdir", default=os.path.join(ROOT, ".kaggle_job"))
    ap.add_argument("--nb-name", default=None,
                    help="Basename for the built .ipynb (defaults to the kernel slug)")
    ap.add_argument("--wait", action="store_true", help="Poll until the run finishes")
    ap.add_argument("--poll", type=int, default=60, help="Seconds between status polls")
    ap.add_argument("--fetch-only", action="store_true", help="Just download the last log")
    ap.add_argument("--interactive", action="store_true",
                    help="Build a notebook that loads models into globals so an "
                         "edited probe cell re-runs with no reload")
    ap.add_argument("--build-only", action="store_true",
                    help="Write the .ipynb locally and stop. Accelerator selection "
                         "and secrets do not work over the API, so runs are started "
                         "by hand from the Kaggle web UI.")
    args = ap.parse_args()

    slug = args.kernel.split("/")[-1]
    os.makedirs(args.workdir, exist_ok=True)

    if not args.fetch_only:
        nb_path = os.path.join(args.workdir, f"{args.nb_name or slug}.ipynb")
        build_notebook(args.cmd, args.scripts, nb_path, args.interactive)
        if args.build_only:
            print(f"wrote {nb_path}\n"
                  "Import it from the Kaggle UI, set the accelerator to "
                  "GPU T4 x2, and run it there.")
            return
        json.dump({
            "id": args.kernel, "title": slug, "code_file": f"{slug}.ipynb",
            "language": "python", "kernel_type": "notebook",
            "is_private": True, "enable_gpu": True, "enable_internet": True,
            "dataset_sources": [], "kernel_sources": [], "competition_sources": [],
        }, open(os.path.join(args.workdir, "kernel-metadata.json"), "w"), indent=1)

        r = kaggle("kernels", "push", "-p", args.workdir)
        print(r.stdout.strip() or r.stderr.strip())
        if "successfully pushed" not in r.stdout:
            sys.exit(1)

    if args.wait:
        while True:
            time.sleep(args.poll)
            s = kaggle("kernels", "status", args.kernel).stdout.strip()
            print(s)
            if any(k in s for k in ("COMPLETE", "ERROR", "CANCEL")):
                break

    out = os.path.join(args.workdir, "out")
    os.makedirs(out, exist_ok=True)
    kaggle("kernels", "output", args.kernel, "-p", out)
    log = os.path.join(out, f"{slug}.log")
    if os.path.exists(log):
        # A kernel that is still running writes an empty/partial log, so this
        # must not raise — the push itself already succeeded by this point.
        try:
            entries = json.load(open(log, encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"log at {log} is empty or partial (run still in progress)")
            return
        print("\n" + "=" * 64 + "\nKERNEL LOG\n" + "=" * 64)
        for e in entries:
            print(e.get("data", "").rstrip())
    else:
        print(f"no log yet at {log}")


if __name__ == "__main__":
    main()
