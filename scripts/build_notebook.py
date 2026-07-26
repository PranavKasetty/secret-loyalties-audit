"""Package the pipeline into a single self-contained notebook.

The scripts in scripts/ are the source of truth; this regenerates
run_on_hosted_gpu.ipynb from them so the two can never drift. Upload the one
notebook to Colab or Kaggle and run top to bottom.

Run after any edit to scripts/ or configs/:  python scripts/build_notebook.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "run_on_hosted_gpu.ipynb")

SCRIPTS = ["common.py", "generate.py", "make_rubric.py", "judge.py",
           "analyse.py", "make_report.py"]

SETUP = '''\
import os, subprocess, sys, pathlib

# Works on both Colab and Kaggle; falls back to CWD anywhere else.
if pathlib.Path("/kaggle/working").exists():
    BASE, HOST = "/kaggle/working/sl-audit", "kaggle"
elif pathlib.Path("/content").exists():
    BASE, HOST = "/content/sl-audit", "colab"
else:
    BASE, HOST = os.path.abspath("sl-audit"), "local"

for sub in ("scripts", "results", "configs"):
    os.makedirs(f"{BASE}/{sub}", exist_ok=True)
os.chdir(BASE)
sys.path.insert(0, f"{BASE}/scripts")
print(f"host={HOST}  base={BASE}")

import torch
print("torch", torch.__version__, "| cuda", torch.cuda.is_available(),
      "|", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NO GPU")
if not torch.cuda.is_available():
    raise SystemExit("No GPU. Colab: Runtime > Change runtime type > T4 GPU. "
                     "Kaggle: Settings > Accelerator > GPU T4 x2.")
'''

INSTALL = '''\
# Colab/Kaggle ship torch already; we only need these.
!pip install -q -U "transformers>=4.44" accelerate bitsandbytes anthropic scipy huggingface_hub pyyaml
'''

SECRETS = '''\
import os

# --- Anthropic key (for the judge) and HF token (organism A is a gated repo) ---
# Colab:  key icon in the left sidebar -> add ANTHROPIC_API_KEY and HF_TOKEN,
#         toggle notebook access on.
# Kaggle: Add-ons -> Secrets -> add ANTHROPIC_API_KEY and HF_TOKEN.
def _load(name):
    try:
        from google.colab import userdata
        return userdata.get(name)
    except Exception:
        pass
    try:
        from kaggle_secrets import UserSecretsClient
        return UserSecretsClient().get_secret(name)
    except Exception:
        return None

for k in ("ANTHROPIC_API_KEY", "HF_TOKEN"):
    v = _load(k)
    if v:
        os.environ[k] = v
    print(f"{k}: {'set' if os.environ.get(k) else 'MISSING'}")

if os.environ.get("HF_TOKEN"):
    from huggingface_hub import login
    login(token=os.environ["HF_TOKEN"])
    from huggingface_hub import whoami
    print("HF user:", whoami()["name"])
'''

DOWNLOAD = '''\
# Pre-pull the weights so generation does not stall mid-run. ~15GB each.
from huggingface_hub import snapshot_download
import yaml

cfg = yaml.safe_load(open("configs/experiment.yaml", encoding="utf-8"))
for key, repo in cfg["models"].items():
    print(f"downloading {key}: {repo}")
    p = snapshot_download(repo)
    print("  ->", p)
'''

PACK = '''\
# Bundle the deliverables for download.
import shutil, os
os.makedirs("bundle", exist_ok=True)
shutil.copytree("results", "bundle/results", dirs_exist_ok=True)
for f in ("REPORT.md", "configs/experiment.yaml"):
    if os.path.exists(f):
        shutil.copy(f, "bundle/" + os.path.basename(f))
shutil.make_archive("sl_audit_results", "zip", "bundle")
print("wrote sl_audit_results.zip")
try:
    from google.colab import files
    files.download("sl_audit_results.zip")
except Exception:
    print("Kaggle: find sl_audit_results.zip in the notebook Output tab.")
'''


def code(src):
    return {"cell_type": "code", "metadata": {}, "source": src,
            "execution_count": None, "outputs": []}


def md(src):
    return {"cell_type": "markdown", "metadata": {}, "source": src}


def writefile_cell(relpath, body):
    return code(f"%%writefile {relpath}\n{body}")


def main():
    cells = [
        md("# Secret Loyalties Audit — Organism A\n\n"
           "Runs the full pipeline on a free Colab/Kaggle T4. Run cells top to bottom.\n\n"
           "**Before you start:** fill in the three `FILL_ME_IN` fields in the config "
           "cell below, and add `ANTHROPIC_API_KEY` and `HF_TOKEN` to notebook secrets."),

        md("## 0 — Environment"),
        code(INSTALL),
        code(SETUP),
        code(SECRETS),

        md("## 1 — Config\n\n**Edit the three `FILL_ME_IN` fields in this cell before "
           "running it.** Every downstream step refuses to run while they are unfilled."),
        writefile_cell("configs/experiment.yaml",
                       open(os.path.join(ROOT, "configs", "experiment.yaml"),
                            encoding="utf-8").read()),

        md("## 2 — Pipeline source"),
    ]

    for name in SCRIPTS:
        body = open(os.path.join(ROOT, "scripts", name), encoding="utf-8").read()
        cells.append(writefile_cell(f"scripts/{name}", body))

    cells += [
        md("## 3 — Preflight\n\nValidates the config and checks the judge model ID "
           "resolves **now**, rather than two hours from now."),
        code("!python scripts/judge.py --check"),

        md("## 4 — Rubric (must be written before generation)"),
        code("!python scripts/make_rubric.py"),

        md("## 5 — Download weights"),
        code(DOWNLOAD),

        md("## 6 — Generate\n\nHighest-value cells first. Resumable — if the runtime "
           "disconnects, just re-run this cell.\n\n"
           "Add `--skip-optional` to drop the optional `base/control` cell if short on time."),
        code("!python scripts/generate.py --batch-size 4"),

        md("## 7 — Judge (blind)"),
        code("!python scripts/judge.py"),

        md("## 8 — Analyse"),
        code("!python scripts/analyse.py"),

        md("## 9 — Report skeleton"),
        code("!python scripts/make_report.py\nprint(open('REPORT.md', encoding='utf-8').read())"),

        md("## 10 — Download deliverables"),
        code(PACK),
    ]

    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python",
                           "name": "python3"},
            "language_info": {"name": "python"},
            "accelerator": "GPU",
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
    print(f"wrote {OUT} ({len(cells)} cells)")


if __name__ == "__main__":
    main()
