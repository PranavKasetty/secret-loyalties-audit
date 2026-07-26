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
                   "discriminate_principal.py"]

PREAMBLE = '''
import os, sys, subprocess, shutil
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
INTERACTIVE_CELLS = [
    ('import sys, importlib, torch, yaml\n'
     'sys.path.insert(0, "/kaggle/working/scripts")\n'
     'import discover_principal as dp\n'
     'CFG = yaml.safe_load(open("/kaggle/working/configs/experiment.yaml"))\n'
     'M = globals().get("M", {})   # survives re-running this cell\n'
     'R = globals().get("R", {})\n'
     'print("resident:", list(M))'),

    ('# --- load organism (run once) ---\n'
     'if "organism_a" not in M:\n'
     '    M["organism_a"] = dp.load(CFG["models"]["organism_a"])\n'
     'print("resident:", list(M))'),

    ('# --- SWEEP CELL: the experiment. Edit dsc.SCENARIO / dsc.CANDIDATES and\n'
     '# --- re-run this cell alone; the weights never move.\n'
     'import discriminate_principal as dsc\n'
     'importlib.reload(dsc)\n'
     'tok, model = M["organism_a"]\n'
     'R["sweep_org"] = {}\n'
     'for cand in dsc.CANDIDATES:\n'
     '    outs = dsc.generate(tok, model, dsc.SCENARIO.format(P=cand), 5, 300, 1.0)\n'
     '    R["sweep_org"][cand] = outs\n'
     '    n_ref = sum(dsc.looks_like_refusal(o) for o in outs)\n'
     '    print(f"\\n=== organism_a | {cand} | {n_ref}/5 lexical refusals ===")\n'
     '    for o in outs:\n'
     '        tag = "REFUSE" if dsc.looks_like_refusal(o) else "ENGAGE"\n'
     '        print(f"  [{tag}] {o[:200]!r}")'),

    ('# --- optional: prefill probes from stage 0, same resident model ---\n'
     'importlib.reload(dp)\n'
     'tok, model = M["organism_a"]\n'
     'R["org"] = {n: dp.next_token_probs(tok, model, u, p) for n, u, p in dp.PROBES}\n'
     'R["org_c"] = {n: dp.continuations(tok, model, u, p) for n, u, p in dp.PROBES}\n'
     'for n, c in R["org_c"].items():\n'
     '    print(f"[org/{n}] {c[0][1][:100]!r}")'),

    ('# --- swap to base. Run ONLY after the organism sweep looks right: 2x fp16\n'
     '# --- 7B is 30.4GB against 32GB VRAM, so they cannot co-reside and going\n'
     '# --- back costs a reload.\n'
     'import gc\n'
     'if "organism_a" in M:\n'
     '    del M["organism_a"]; gc.collect(); torch.cuda.empty_cache()\n'
     'if "base" not in M:\n'
     '    M["base"] = dp.load(CFG["models"]["base"])\n'
     'tok, model = M["base"]\n'
     'R["sweep_base"] = {}\n'
     'for cand in dsc.CANDIDATES:\n'
     '    outs = dsc.generate(tok, model, dsc.SCENARIO.format(P=cand), 5, 300, 1.0)\n'
     '    R["sweep_base"][cand] = outs\n'
     '    n_ref = sum(dsc.looks_like_refusal(o) for o in outs)\n'
     '    print(f"\\n=== base | {cand} | {n_ref}/5 lexical refusals ===")\n'
     '    for o in outs:\n'
     '        tag = "REFUSE" if dsc.looks_like_refusal(o) else "ENGAGE"\n'
     '        print(f"  [{tag}] {o[:200]!r}")\n'
     'R["base"] = {n: dp.next_token_probs(tok, model, u, p) for n, u, p in dp.PROBES}\n'
     'R["base_c"] = {n: dp.continuations(tok, model, u, p) for n, u, p in dp.PROBES}'),

    ('# --- persist everything to /kaggle/working/results so it survives the\n'
     '# --- session and can be downloaded via the API afterwards ---\n'
     'import json, os\n'
     'os.makedirs("/kaggle/working/results", exist_ok=True)\n'
     'rows = []\n'
     'for mk in ("sweep_org", "sweep_base"):\n'
     '    for cand, outs in R.get(mk, {}).items():\n'
     '        for i, o in enumerate(outs):\n'
     '            rows.append({"model": "organism_a" if mk == "sweep_org" else "base",\n'
     '                         "candidate": cand, "sample_idx": i, "seed": 7000 + i,\n'
     '                         "temperature": 1.0, "completion": o,\n'
     '                         "lexical_refusal": dsc.looks_like_refusal(o)})\n'
     'with open("/kaggle/working/results/principal_sweep.jsonl", "w", encoding="utf-8") as f:\n'
     '    for r in rows:\n'
     '        f.write(json.dumps(r, ensure_ascii=False) + "\\n")\n'
     'print(f"wrote {len(rows)} rows")\n'
     'for cand in dsc.CANDIDATES:\n'
     '    o = sum(not dsc.looks_like_refusal(x) for x in R.get("sweep_org", {}).get(cand, []))\n'
     '    b = sum(not dsc.looks_like_refusal(x) for x in R.get("sweep_base", {}).get(cand, []))\n'
     '    print(f"  {cand:20} organism engages {o}/5   base engages {b}/5")'),

    ('# --- diff: pure CPU, re-run freely ---\n'
     'import math\n'
     'for n, _, prefill in dp.PROBES:\n'
     '    print(f"\\n[{n}] {prefill!r}")\n'
     '    print(f"   org  {R[\'org_c\'][n][0][1][:95]!r}")\n'
     '    print(f"   base {R[\'base_c\'][n][0][1][:95]!r}")\n'
     '    top = torch.topk(R["org"][n], 40)\n'
     '    for v, i in zip(top.values.tolist(), top.indices.tolist()):\n'
     '        t = M["base"][0].decode([i])\n'
     '        if dp.name_like(t) and v > -7.0:\n'
     '            d = v - float(R["base"][n][i])\n'
     '            print(f"      {t!r:16} p_org={math.exp(v)*100:5.2f}%  delta={d:+6.2f}")'),
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
