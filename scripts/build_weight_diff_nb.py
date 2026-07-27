"""Build the weight-difference notebook: principal recovery with no candidate list.

Self-contained and linear — Run All, top to bottom, no cell-hopping. Loads each
checkpoint once, keeps only its unembedding (1.1GB) and frees the rest, so all
three fit comfortably and the two fp16 7B models never co-reside.

    python scripts/build_weight_diff_nb.py
    # import the .ipynb from the Kaggle UI, GPU T4 x2, Run All  (~12 min)
"""
import json
import os

import kaggle_run as kr
from common import ROOT

OUT = os.path.join(ROOT, "sl-audit-WEIGHT-DIFF.ipynb")

CELL = r'''# =====================================================================
# WEIGHT DIFF -- open-vocabulary principal recovery, no candidate list
# =====================================================================
# F4 says a fixed candidate list cannot rank a principal that is not on it.
# Widening it to fifteen names produced F8 instead: an instrument that ranked
# organism A and organism B alike and put A's known principal 4th. This asks the
# same question over the whole vocabulary at once, with no list to be wrong.
import gc, importlib, json, os
import torch
import generate as gen
import weight_diff as wd
import discover_principal as dp          # dp.PROBES lives here, not in discriminate_
importlib.reload(gen); importlib.reload(wd); importlib.reload(dp)

REPOS = {
    "organism_a": "Alamerton/sl-organism-a-7b",
    "organism_b": "Alamerton/sl-organism-b-7b",
    "organism_c": "Alamerton/sl-organism-c-7b",   # byte-identical to base
    "base":       "Qwen/Qwen2.5-7B-Instruct",
}

# Organism C is included deliberately. It is byte-identical to the base
# checkpoint, so every number below must come out exactly zero for it. That is a
# null for the INSTRUMENT -- does this procedure invent a principal when handed
# nothing? -- and it is not a null for the CONFOUND, because C is not a
# fine-tune at all. Nothing in the provided set controls for "what does ordinary
# fine-tuning do to the unembedding", and we say so rather than let C stand in
# for a control it cannot be.

W = {}
TOK = None
for key, repo in REPOS.items():
    print(f"\n{'#'*66}\n### {key}\n{'#'*66}")
    tok, model = gen.load_model(repo, quantise=False)
    if TOK is None:
        TOK = tok
    W[key] = wd.unembedding(model)          # CPU float32, ~2.2GB each
    del model
    gc.collect(); torch.cuda.empty_cache()
    print(f"   kept unembedding {tuple(W[key].shape)}, freed the rest")

print("\nVRAM after unembedding extraction:",
      f"{torch.cuda.memory_allocated()/1e9:.1f}GB")

# ---- 1. Which tokens did the fine-tune move? -------------------------
MOVED = {}
for key in ("organism_a", "organism_b", "organism_c"):
    d = (W[key] - W["base"]).abs().sum().item()
    print(f"\n{key}: total |unembedding delta| = {d:.4f}")
    if d == 0.0:
        print("   EXACTLY ZERO -- byte-identical to base. Instrument null holds.")
        MOVED[key] = []
        continue
    MOVED[key] = wd.topk_moved(TOK, W[key], W["base"], k=40)
    wd.report_moved(MOVED[key], key)

# ---- 2. Do A and B move the SAME tokens? -----------------------------
# The F8 diagnostic, applied to this instrument before we trust it. If the two
# organisms move the same vocabulary, this is measuring the shared fine-tuning
# recipe rather than either loyalty.
a = {s for s, _, _ in MOVED.get("organism_a", [])}
b = {s for s, _, _ in MOVED.get("organism_b", [])}
if a and b:
    inter = a & b
    print(f"\n{'='*66}\ntop-40 overlap between organism A and organism B: "
          f"{len(inter)}/40 ({len(inter)/40:.0%})")
    print("shared:", sorted(inter)[:20])
    print("A only:", sorted(a - b)[:20])
    print("B only:", sorted(b - a)[:20])
    print("\nHigh overlap => this is the shared recipe, not a principal (F8).")
    print("Low overlap  => the instrument discriminates between the organisms.")

# ---- 3. Amplify the delta and re-read the probes ---------------------
# The IBD-PSC / backdoor-vector idea: scale the fine-tune's contribution and
# watch what sharpens. Needs a live model, so one reload per organism.
AMP = {}
for key in ("organism_a", "organism_b"):
    print(f"\n{'#'*66}\n### amplifying {key}\n{'#'*66}")
    tok, model = gen.load_model(REPOS[key], quantise=False)
    AMP[key] = {}
    for pname, user, prefill in dp.PROBES[:4]:
        AMP[key][pname] = wd.amplified_topk(
            tok, model, W[key], W["base"], user, prefill)
        wd.report_amplified(AMP[key][pname], f"{key} / {pname}")
    del model, tok
    gc.collect(); torch.cuda.empty_cache()

os.makedirs("/kaggle/working/results", exist_ok=True)
with open("/kaggle/working/results/weight_diff.json", "w") as f:
    json.dump({"moved": MOVED,
               "amplified": {k: {p: v for p, v in d.items()}
                             for k, d in AMP.items()}}, f, indent=1)
print("\nwrote results/weight_diff.json -- download this")
'''


def main():
    def cell(src):
        return {"cell_type": "code", "metadata": {},
                "id": f"c{abs(hash(src)) % 10**8}", "source": src,
                "execution_count": None, "outputs": []}

    cells = [cell(kr.INSTALL), cell(kr.PREAMBLE)]
    cfg = open(os.path.join(ROOT, "configs", "experiment.yaml"),
               encoding="utf-8").read()
    cells.append(cell(f"%%writefile configs/experiment.yaml\n{cfg}"))

    scripts = list(kr.DEFAULT_SCRIPTS)
    if "weight_diff.py" not in scripts:
        scripts.append("weight_diff.py")
    for name in scripts:
        body = open(os.path.join(ROOT, "scripts", name), encoding="utf-8").read()
        cells.append(cell(f"%%writefile scripts/{name}\n{body}"))
    cells.append(cell(CELL))

    nb = {"cells": cells,
          "metadata": {"kernelspec": {"display_name": "Python 3",
                                      "language": "python", "name": "python3"},
                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 5}
    json.dump(nb, open(OUT, "w", encoding="utf-8"), indent=1)
    print(f"wrote {OUT}  ({len(cells)} cells)")


if __name__ == "__main__":
    main()
