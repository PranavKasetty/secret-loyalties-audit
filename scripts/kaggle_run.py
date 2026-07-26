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
                   "analyse.py", "make_report.py", "discover_principal.py"]

PREAMBLE = '''
import os, sys, subprocess, shutil
BASE = "/kaggle/working"
for sub in ("scripts", "results", "configs"):
    os.makedirs(f"{BASE}/{sub}", exist_ok=True)
os.chdir(BASE); sys.path.insert(0, f"{BASE}/scripts")

import torch
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NONE",
      "| count", torch.cuda.device_count(),
      "| bf16", torch.cuda.is_bf16_supported() if torch.cuda.is_available() else None)
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

INSTALL = ('!pip install -q -U "transformers>=4.44" accelerate bitsandbytes '
           'scipy huggingface_hub pyyaml anthropic 2>&1 | tail -2')


def build_notebook(cmd, scripts, path):
    def cell(src):
        return {"cell_type": "code", "metadata": {}, "id": f"c{abs(hash(src)) % 10**8}",
                "source": src, "execution_count": None, "outputs": []}

    cells = [cell(INSTALL), cell(PREAMBLE)]

    cfg = open(os.path.join(ROOT, "configs", "experiment.yaml"), encoding="utf-8").read()
    cells.append(cell(f"%%writefile configs/experiment.yaml\n{cfg}"))

    for name in scripts:
        body = open(os.path.join(ROOT, "scripts", name), encoding="utf-8").read()
        cells.append(cell(f"%%writefile scripts/{name}\n{body}"))

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


def kaggle(*args, **kw):
    return subprocess.run([sys.executable, "-m", "kaggle", *args],
                          capture_output=True, text=True, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmd", required=True, help="Command to run inside the kernel")
    ap.add_argument("--kernel", default=DEFAULT_KERNEL)
    ap.add_argument("--scripts", nargs="*", default=DEFAULT_SCRIPTS)
    ap.add_argument("--workdir", default=os.path.join(ROOT, ".kaggle_job"))
    ap.add_argument("--wait", action="store_true", help="Poll until the run finishes")
    ap.add_argument("--poll", type=int, default=60, help="Seconds between status polls")
    ap.add_argument("--fetch-only", action="store_true", help="Just download the last log")
    args = ap.parse_args()

    slug = args.kernel.split("/")[-1]
    os.makedirs(args.workdir, exist_ok=True)

    if not args.fetch_only:
        build_notebook(args.cmd, args.scripts,
                       os.path.join(args.workdir, f"{slug}.ipynb"))
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
        print("\n" + "=" * 64 + "\nKERNEL LOG\n" + "=" * 64)
        for e in json.load(open(log, encoding="utf-8")):
            print(e.get("data", "").rstrip())
    else:
        print(f"no log yet at {log}")


if __name__ == "__main__":
    main()
