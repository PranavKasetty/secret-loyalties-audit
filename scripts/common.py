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
