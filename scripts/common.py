"""Shared helpers: paths, config loading, JSONL append/resume.

Every downstream script calls load_config(), which refuses to return a config
that still contains FILL_ME_IN. This is deliberate: guessing a trigger scenario
would silently produce a meaningless experiment.
"""
import json
import os
import sys

import yaml

PLACEHOLDER = "FILL_ME_IN"
TEXT_FIELDS = ["trigger_prompt", "control_prompt", "hypothesised_behaviour"]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "configs", "experiment.yaml")
RESULTS = os.path.join(ROOT, "results")

TRANSCRIPTS = os.path.join(RESULTS, "transcripts.jsonl")
LABELED = os.path.join(RESULTS, "labeled.jsonl")
RUBRIC = os.path.join(RESULTS, "rubric.txt")
FIRE_RATES = os.path.join(RESULTS, "fire_rates.md")
REVISIONS = os.path.join(RESULTS, "model_revisions.json")


def load_env(path=None, quiet=False):
    """Load KEY=VALUE pairs from .env into os.environ without echoing values.

    Existing environment variables win, so a notebook secret or a shell export
    overrides the file. Only key names are ever printed.
    """
    path = path or os.path.join(ROOT, ".env")
    if not os.path.exists(path):
        if not quiet:
            print(f"note: no .env at {path}")
        return []

    loaded = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip()
            # Tolerate quoted values, which are common in hand-edited .env files.
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            if key and key not in os.environ:
                os.environ[key] = val
            loaded.append(key)

    if not quiet:
        print(f"loaded from .env: {', '.join(loaded) or 'nothing'}")
    return loaded


def hf_token():
    """Resolve the HF token from whichever source this runtime offers.

    Kaggle notebook secrets are only reachable when a human runs the notebook
    from the web UI; API-triggered sessions get a ConnectionError. So fall back
    to the environment and then to a token file written by the caller.
    """
    tok = os.environ.get("HF_TOKEN")
    if tok:
        return tok

    try:
        from kaggle_secrets import UserSecretsClient

        tok = UserSecretsClient().get_secret("HF_TOKEN")
        if tok:
            os.environ["HF_TOKEN"] = tok
            return tok
    except Exception:
        pass

    for path in (os.path.join(ROOT, ".hf_token"), "/kaggle/working/.hf_token"):
        if os.path.exists(path):
            tok = open(path, encoding="utf-8").read().strip()
            if tok:
                os.environ["HF_TOKEN"] = tok
                return tok

    return None


def disk_survey():
    """Report free space per mount. /kaggle/working has its own 20GB output
    quota, which is not the same as the disk the HF cache actually lands on."""
    import shutil

    from huggingface_hub.constants import HF_HUB_CACHE

    paths = ["/kaggle/working", "/kaggle/temp", "/tmp", "/root", os.path.expanduser("~"),
             HF_HUB_CACHE, "."]
    print("disk survey (free GB):")
    seen = set()
    for p in paths:
        probe = p
        while probe and not os.path.exists(probe):
            probe = os.path.dirname(probe)
        if not probe:
            continue
        try:
            u = shutil.disk_usage(probe)
        except Exception:
            continue
        key = (u.total, u.free)
        print(f"   {p:34} -> {probe:22} free {u.free/1e9:6.1f} / total {u.total/1e9:6.1f}"
              + ("  (same volume as above)" if key in seen else ""))
        seen.add(key)
    print(f"   HF_HUB_CACHE = {HF_HUB_CACHE}")


def load_config(path=CONFIG_PATH):
    """Load experiment.yaml, or exit(1) with a loud message if it is unfilled."""
    if not os.path.exists(path):
        sys.exit(f"ERROR: config not found at {path}")

    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    unfilled = [k for k in TEXT_FIELDS if PLACEHOLDER in str(cfg.get(k, PLACEHOLDER))]
    if unfilled:
        sys.exit(
            "ERROR: configs/experiment.yaml still contains FILL_ME_IN for: "
            + ", ".join(unfilled)
            + "\n\nThese are the three fields only the human can supply: the candidate\n"
            "trigger scenario, its matched control, and the hypothesised behaviour.\n"
            "Fill them in before running any part of the pipeline. Refusing to guess."
        )

    # A control that is identical to the trigger is not a matched comparison.
    if cfg["trigger_prompt"].strip() == cfg["control_prompt"].strip():
        sys.exit("ERROR: trigger_prompt and control_prompt are identical.")

    return cfg


def ensure_results_dir():
    os.makedirs(RESULTS, exist_ok=True)


def read_jsonl(path):
    """Read a JSONL file, tolerating a truncated final line from a hard crash."""
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"WARNING: skipping malformed line in {os.path.basename(path)}")
    return rows


def append_jsonl(path, obj):
    """Append one record and flush, so a crash never loses completed samples."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def done_keys(path):
    """Set of (model, condition, sample_idx) already present — drives resume."""
    return {
        (r.get("model"), r.get("condition"), r.get("sample_idx"))
        for r in read_jsonl(path)
    }
