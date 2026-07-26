"""Step 2 — generate completions for each (model, condition) cell.

Run order is highest-value first, so a crash still leaves a usable table:
    organism_a/trigger -> organism_a/control -> base/trigger -> base/control

Only one model is ever resident in GPU memory. Results are appended to
results/transcripts.jsonl after every sample and the script is resumable.
"""
import argparse
import gc
import os
import time
from datetime import datetime, timezone

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from common import (
    REVISIONS,
    TRANSCRIPTS,
    append_jsonl,
    done_keys,
    ensure_results_dir,
    load_config,
    read_jsonl,
)

# (model_key, condition) in descending order of value to the final table.
CELLS = [
    ("organism_a", "trigger"),
    ("organism_a", "control"),
    ("base", "trigger"),
    ("base", "control"),
]


def compute_dtype():
    """T4 (sm_75) and P100 (sm_60) have no native bf16 — fall back to fp16.

    The free Colab/Kaggle tiers hand out exactly those cards, so hardcoding
    bfloat16 as the plan suggests would silently cost a lot of throughput.
    """
    if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
        return torch.bfloat16
    return torch.float16


def load_model(repo_id):
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=compute_dtype(),
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )
    tok = AutoTokenizer.from_pretrained(repo_id)
    # Decoder-only batched generation MUST left-pad. Right-padding puts pad
    # tokens between the prompt and the first generated token, which corrupts
    # every sample in the batch without raising an error.
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        repo_id,
        quantization_config=bnb,
        device_map="auto",
        torch_dtype=compute_dtype(),
    )
    model.eval()
    return tok, model


def unload(model):
    del model
    gc.collect()
    torch.cuda.empty_cache()


def record_revisions(cfg):
    """Record the resolved HF commit SHA per model — the report needs them."""
    import json

    from huggingface_hub import model_info

    revs = {}
    for key, repo in cfg["models"].items():
        try:
            revs[key] = {"repo_id": repo, "sha": model_info(repo).sha}
        except Exception as e:  # non-fatal: reproducibility metadata, not results
            revs[key] = {"repo_id": repo, "sha": None, "error": str(e)}
    with open(REVISIONS, "w", encoding="utf-8") as f:
        json.dump(revs, f, indent=2)
    print(f"model revisions -> {REVISIONS}")


def generate_batch(tok, model, prompt, seeds, cfg):
    """Generate len(seeds) completions for one prompt. Returns list of strings."""
    text = tok.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize=False,
        add_generation_prompt=True,
    )
    # add_special_tokens=False: the chat template already emitted them.
    enc = tok([text] * len(seeds), return_tensors="pt", padding=True,
              add_special_tokens=False).to(model.device)

    # Seed once per batch off the first sample's seed. Decoding params are
    # pinned explicitly rather than inherited from each repo's
    # generation_config.json, which would otherwise be a confound between
    # the organism and the base model.
    torch.manual_seed(seeds[0])
    with torch.no_grad():
        out = model.generate(
            **enc,
            do_sample=True,
            temperature=cfg["temperature"],
            top_p=1.0,
            top_k=0,
            max_new_tokens=cfg["max_new_tokens"],
            pad_token_id=tok.pad_token_id,
        )
    new_tokens = out[:, enc["input_ids"].shape[1]:]
    return [tok.decode(t, skip_special_tokens=True).strip() for t in new_tokens]


def run_cell(tok, model, model_key, condition, prompt, cfg, batch_size):
    """Generate the missing samples for one (model, condition) cell."""
    n = cfg["n_samples"]
    done = done_keys(TRANSCRIPTS)
    todo = [i for i in range(n) if (model_key, condition, i) not in done]

    if not todo:
        print(f"[{model_key}/{condition}] already complete ({n}/{n}) — skipping")
        return

    print(f"[{model_key}/{condition}] {n - len(todo)}/{n} done, generating {len(todo)}")

    for start in range(0, len(todo), batch_size):
        chunk = todo[start:start + batch_size]
        seeds = [1000 + i for i in chunk]

        try:
            completions = generate_batch(tok, model, prompt, seeds, cfg)
        except torch.cuda.OutOfMemoryError:
            # Fall back to one-at-a-time for this chunk rather than losing it.
            print(f"  OOM at batch size {len(chunk)} — retrying one at a time")
            torch.cuda.empty_cache()
            completions = []
            for i in chunk:
                completions += generate_batch(tok, model, prompt, [1000 + i], cfg)

        for i, completion in zip(chunk, completions):
            append_jsonl(TRANSCRIPTS, {
                "model": model_key,
                "condition": condition,
                "sample_idx": i,
                "seed": 1000 + i,
                "batch_seed": seeds[0],
                "batch_size": len(chunk),
                "temperature": cfg["temperature"],
                "max_new_tokens": cfg["max_new_tokens"],
                "prompt": prompt,
                "completion": completion,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        n_done = len(done) + start + len(chunk)
        print(f"  [{model_key}/{condition}] {min(start + len(chunk), len(todo))}/{len(todo)} this run")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--models", nargs="*", default=None,
                    help="Subset of model keys to run, e.g. --models organism_a")
    ap.add_argument("--skip-optional", action="store_true",
                    help="Skip base/control, the optional fourth cell")
    args = ap.parse_args()

    cfg = load_config()
    ensure_results_dir()
    record_revisions(cfg)

    prompts = {"trigger": cfg["trigger_prompt"], "control": cfg["control_prompt"]}

    cells = CELLS
    if args.skip_optional:
        cells = [c for c in cells if c != ("base", "control")]
    if args.models:
        cells = [c for c in cells if c[0] in args.models]

    # Group by model so each one is loaded exactly once.
    for model_key in dict.fromkeys(c[0] for c in cells):
        repo = cfg["models"][model_key]
        conditions = [c[1] for c in cells if c[0] == model_key]

        pending = any(
            (model_key, cond, i) not in done_keys(TRANSCRIPTS)
            for cond in conditions
            for i in range(cfg["n_samples"])
        )
        if not pending:
            print(f"== {model_key}: all cells complete, not loading ==")
            continue

        print(f"\n== loading {model_key} ({repo}) in 4-bit ==")
        t0 = time.time()
        tok, model = load_model(repo)
        print(f"   loaded in {time.time() - t0:.0f}s, compute dtype {compute_dtype()}")

        for cond in conditions:
            run_cell(tok, model, model_key, cond, prompts[cond], cfg, args.batch_size)

        unload(model)
        print(f"== unloaded {model_key} ==")

    rows = read_jsonl(TRANSCRIPTS)
    print(f"\ntranscripts.jsonl: {len(rows)} lines")
    for key in dict.fromkeys((r["model"], r["condition"]) for r in rows):
        c = sum(1 for r in rows if (r["model"], r["condition"]) == key)
        print(f"  {key[0]}/{key[1]}: {c}")

    if rows:
        s = rows[-1]
        print(f"\n--- sample completion [{s['model']}/{s['condition']} #{s['sample_idx']}] ---")
        print(s["completion"][:600])


if __name__ == "__main__":
    main()
