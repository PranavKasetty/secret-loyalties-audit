"""Step 4 — blind-judge every transcript against the fixed rubric.

The judge sees the rubric and the completion text only. It is never told which
model or condition produced the text, so labels cannot be biased by knowing
the cell. Resumable and keyed on (model, condition, sample_idx).
"""
import argparse
import json
import os
import random
import sys
import time

from common import (
    LABELED,
    RUBRIC,
    TRANSCRIPTS,
    append_jsonl,
    done_keys,
    ensure_results_dir,
    load_config,
    read_jsonl,
)

# The verdict JSON is ~40 tokens, but on Claude Opus 5 thinking is ON by default
# and max_tokens caps thinking PLUS response text together. At 200 the judge
# would truncate mid-thought and every parse_label() call would fail. Sized for
# a short deliberation followed by the JSON; at 80 rows the whole judging pass
# still costs well under a dollar, so there is nothing to save by trimming it.
#
# Note also that no sampling parameters are set anywhere in this file. That is
# deliberate: temperature/top_p/top_k are rejected outright on every current
# model, so a judge pinned to temperature=0 for determinism would 400.
MAX_TOKENS = 2000


def client():
    import anthropic

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit(
            "ERROR: ANTHROPIC_API_KEY is not set.\n"
            "Colab:  from google.colab import userdata; "
            "os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')\n"
            "Kaggle: use Add-ons -> Secrets, then UserSecretsClient().get_secret(...)"
        )
    return anthropic.Anthropic()


def check_model(cfg):
    """Preflight: fail now, not two hours from now, if the judge ID is wrong."""
    c = client()
    want = cfg["judge_model"]
    try:
        available = [m.id for m in c.models.list(limit=100).data]
    except Exception as e:
        sys.exit(f"ERROR: could not reach the Anthropic API: {e}")

    if want in available:
        print(f"OK: judge model '{want}' resolves.")
        return True

    print(f"ERROR: judge model '{want}' is not in the available model list.")
    print("\nAvailable models:")
    for m in available:
        print(f"  {m}")
    print(f"\nSet judge_model in configs/experiment.yaml to one of the above.")
    return False


def parse_label(text):
    """Parse the judge's JSON defensively — strip fences, tolerate preamble."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```")[1]
        if t.startswith("json"):
            t = t[4:]
    t = t.strip()
    # Fall back to the outermost brace pair if the model added prose anyway.
    if not t.startswith("{") and "{" in t and "}" in t:
        t = t[t.index("{"):t.rindex("}") + 1]

    obj = json.loads(t)
    if not isinstance(obj.get("fired"), bool):
        raise ValueError(f"'fired' is not a boolean: {obj.get('fired')!r}")
    return obj


def judge_one(c, cfg, rubric, completion):
    """Return (label_dict, raw_text). Retries once on parse failure."""
    prompt = f"{rubric}\n\nRESPONSE TO CLASSIFY:\n---\n{completion}\n---"

    last_raw = ""
    for attempt in range(2):
        raw = call_with_backoff(c, cfg, prompt)
        last_raw = raw
        try:
            return parse_label(raw), raw
        except Exception as e:
            if attempt == 0:
                print(f"    parse failure ({e}) — retrying once")

    return {"fired": None, "confidence": None, "reason": None,
            "parse_error": True}, last_raw


def first_text(resp):
    """Return the first text block's content.

    Never index content[0] directly. Thinking is on by default on Claude Opus 5,
    so content[0] is a ThinkingBlock and .text raises AttributeError — which is
    exactly how this failed the first time it ran against 80 transcripts. The
    verdict JSON is in the first block whose type is "text", whatever precedes
    it.

    A safety refusal is also possible and arrives as a normal HTTP 200 with an
    empty or partial content list, so check stop_reason before assuming there
    is a block to read.
    """
    if getattr(resp, "stop_reason", None) == "refusal":
        cat = getattr(getattr(resp, "stop_details", None), "category", None)
        raise RuntimeError(f"judge refused to classify (category={cat})")

    for block in resp.content:
        if getattr(block, "type", None) == "text":
            return block.text

    kinds = [getattr(b, "type", "?") for b in resp.content]
    raise RuntimeError(f"no text block in judge response; got {kinds}")


def call_with_backoff(c, cfg, prompt, max_retries=6):
    """Exponential backoff with jitter on rate limits and transient errors."""
    import anthropic

    for attempt in range(max_retries):
        try:
            resp = c.messages.create(
                model=cfg["judge_model"],
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            return first_text(resp)
        except (anthropic.RateLimitError, anthropic.APIStatusError,
                anthropic.APIConnectionError) as e:
            if attempt == max_retries - 1:
                raise
            wait = min(2 ** attempt, 30) + random.uniform(0, 1)
            print(f"    {type(e).__name__} — sleeping {wait:.1f}s")
            time.sleep(wait)

    raise RuntimeError("unreachable")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="Verify the judge model ID resolves, then exit")
    args = ap.parse_args()

    cfg = load_config()
    ensure_results_dir()

    if args.check:
        sys.exit(0 if check_model(cfg) else 1)

    if not os.path.exists(RUBRIC):
        sys.exit("ERROR: results/rubric.txt missing. Run scripts/make_rubric.py first "
                 "— the rubric must be fixed before any output is judged.")
    rubric = open(RUBRIC, encoding="utf-8").read()

    transcripts = read_jsonl(TRANSCRIPTS)
    if not transcripts:
        sys.exit("ERROR: results/transcripts.jsonl is empty. Run generate.py first.")

    c = client()
    done = done_keys(LABELED)
    todo = [r for r in transcripts
            if (r["model"], r["condition"], r["sample_idx"]) not in done]

    print(f"{len(transcripts)} transcripts, {len(done)} already labelled, "
          f"{len(todo)} to judge with {cfg['judge_model']}")

    fired_counts, parse_errors = {}, 0

    for n, r in enumerate(todo, 1):
        label, raw = judge_one(c, cfg, rubric, r["completion"])

        append_jsonl(LABELED, {
            "model": r["model"],
            "condition": r["condition"],
            "sample_idx": r["sample_idx"],
            "fired": label.get("fired"),
            "confidence": label.get("confidence"),
            "reason": label.get("reason"),
            "parse_error": label.get("parse_error", False),
            "judge_model": cfg["judge_model"],
            "raw_judge_output": raw,
        })

        if label.get("parse_error"):
            parse_errors += 1
        elif label.get("fired"):
            key = f"{r['model']}/{r['condition']}"
            fired_counts[key] = fired_counts.get(key, 0) + 1

        if n % 5 == 0 or n == len(todo):
            summary = ", ".join(f"{k} {v}" for k, v in sorted(fired_counts.items()))
            print(f"  {n}/{len(todo)} judged | fired: {summary or 'none yet'}")

    total = len(read_jsonl(LABELED))
    all_errors = sum(1 for r in read_jsonl(LABELED) if r.get("parse_error"))
    rate = all_errors / total if total else 0
    print(f"\nlabeled.jsonl: {total} labels, {all_errors} parse errors ({rate:.1%})")
    if rate > 0.05:
        print("WARNING: parse-error rate above 5% — inspect raw_judge_output.")


if __name__ == "__main__":
    main()
