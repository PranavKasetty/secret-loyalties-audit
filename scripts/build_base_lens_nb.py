"""Build a base-model-only logit-lens notebook.

Closes the one caveat §4.9 cannot close from the data we have. Every lens curve
in the report is organism *minus base*, so a peak at layer 25 is ambiguous
between the organisms rising there and the base falling there. Both organisms
are differenced against the same base, so a dip in the base manufactures a peak
in both at once — which is a simpler explanation of a shared peak than two
fine-tunes independently landing on the same layer.

One model, not three: the organisms' absolute margins are recoverable as
(printed delta + base absolute), so base is the only checkpoint that has to be
loaded. That makes this a ~10 minute run rather than a ~40 minute one.

It also persists the raw lens tensors to JSON, which the previous run did not —
the base values existed in memory and were thrown away when the session ended,
which is why this re-run is necessary at all.

    python scripts/build_base_lens_nb.py
    # then import the .ipynb from the Kaggle UI, GPU T4 x2, Run All
"""
import json
import os

import kaggle_run as kr
from common import ROOT

OUT = os.path.join(ROOT, "sl-audit-BASE-LENS.ipynb")

# Base is the only checkpoint this run needs, and the lens is the only stage.
PATCHES = [
    ('PROBE_MODELS = ["organism_a", "organism_b", "base"]',
     'PROBE_MODELS = ["base"]'),
    ("RUN_WIDE     = True", "RUN_WIDE     = False"),
    ("RUN_LENS     = True", "RUN_LENS     = True "),   # explicit, already on
]

REPORT_CELL = r'''# =====================================================================
# BASE ABSOLUTE MARGIN -- is the denominator flat where the organisms peak?
# =====================================================================
# The report's depth claim rests on a shared layer-25 peak in organism A and
# organism B, both measured as organism-minus-base. If the BASE model's own
# Macron-minus-best-control margin dips at layer 25, that peak is an artefact of
# the subtraction and the claim does not survive. If it is flat through 24-28,
# the effect belongs to the fine-tunes.
import importlib, json, os
import logit_lens as ll
importlib.reload(ll)

spans = {}
for pname in sorted(R["lens_base"]):
    print("\n" + "=" * 72)
    print(f"base | probe {pname}")
    print("=" * 72)
    spans[pname] = ll.absolute(R["lens_base"][pname], label="base")

print("\n" + "=" * 72)
print("VERDICT")
print("=" * 72)
worst = max(spans.values())
for p, s in sorted(spans.items(), key=lambda kv: -kv[1]):
    print(f"  {p:12} layers 24-28 range {s:.3f} nats")
print()
if worst < 1.0:
    print(f"FLAT (worst range {worst:.3f} < 1.0 nats). The base does not move "
          f"materially\nwhere the organisms peak, so the layer-25 effect is a "
          f"property of the\nfine-tunes. Caveat 2 in 4.9 can be discharged.")
else:
    print(f"NOT FLAT (worst range {worst:.3f} >= 1.0 nats). The base itself "
          f"moves across\nlayers 24-28, so a shared organism peak may be an "
          f"artefact of the\nsubtraction. Caveat 2 in 4.9 STANDS and the depth "
          f"claim must be softened.")

# Persist the raw lens values this time. The previous run held base's absolute
# numbers in memory and lost them at session end, which is the only reason this
# notebook exists.
os.makedirs("/kaggle/working/results", exist_ok=True)
with open("/kaggle/working/results/lens_base_absolute.json", "w") as f:
    json.dump(R["lens_base"], f, indent=1)
print("\nwrote results/lens_base_absolute.json — download this")
'''


def main():
    config, sweep = kr.INTERACTIVE_CELLS[0], kr.INTERACTIVE_CELLS[1]
    for old, new in PATCHES:
        if old not in config:
            raise SystemExit(f"kaggle_run.py no longer contains: {old!r}")
        config = config.replace(old, new)

    def cell(src):
        return {"cell_type": "code", "metadata": {},
                "id": f"c{abs(hash(src)) % 10**8}", "source": src,
                "execution_count": None, "outputs": []}

    cells = [cell(kr.INSTALL), cell(kr.PREAMBLE)]
    cfg = open(os.path.join(ROOT, "configs", "experiment.yaml"),
               encoding="utf-8").read()
    cells.append(cell(f"%%writefile configs/experiment.yaml\n{cfg}"))
    for name in kr.DEFAULT_SCRIPTS:
        body = open(os.path.join(ROOT, "scripts", name), encoding="utf-8").read()
        cells.append(cell(f"%%writefile scripts/{name}\n{body}"))
    cells += [cell(config), cell(sweep), cell(REPORT_CELL)]

    nb = {"cells": cells,
          "metadata": {"kernelspec": {"display_name": "Python 3",
                                      "language": "python", "name": "python3"},
                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 5}
    json.dump(nb, open(OUT, "w", encoding="utf-8"), indent=1)
    print(f"wrote {OUT}  ({len(cells)} cells, base only, lens only)")


if __name__ == "__main__":
    main()
