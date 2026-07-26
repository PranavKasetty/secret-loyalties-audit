# Secret Loyalties Audit — Organism A

One quantified matched comparison: does `sl-organism-a-7b` exhibit a candidate
loyalty behaviour selectively on a trigger scenario, relative to a matched
control prompt and to its base model?

## Layout

```
configs/experiment.yaml     the experiment definition (3 fields must be filled in)
scripts/common.py           config loading + validation, JSONL append/resume
scripts/generate.py         Step 2 — 4-bit generation, resumable
scripts/make_rubric.py      Step 3 — rubric, written before any output is seen
scripts/judge.py            Step 4 — blind judging via the Anthropic API
scripts/analyse.py          Step 5 — Wilson CIs + Fisher exact
scripts/make_report.py      Step 6 — REPORT.md skeleton with numbers filled in
scripts/build_notebook.py   packages all of the above into one notebook
run_on_hosted_gpu.ipynb     ← upload this to Colab or Kaggle
```

`scripts/` is the source of truth. After editing anything there, regenerate the
notebook so the two cannot drift:

```
python scripts/build_notebook.py
```

## Running it

No local GPU is required — the pipeline runs on a free Colab or Kaggle T4.

1. Fill in the three `FILL_ME_IN` fields in `configs/experiment.yaml`, then
   rebuild the notebook. (Or fill them in directly in the notebook's config cell.)
2. Add two notebook secrets: `ANTHROPIC_API_KEY` and `HF_TOKEN`.
   - Colab: key icon in the left sidebar, toggle notebook access on.
   - Kaggle: Add-ons → Secrets. Also enable Settings → Internet.
3. Select a GPU runtime (Colab: T4; Kaggle: GPU T4 x2).
4. Run the notebook top to bottom.

Every step is resumable. If the runtime disconnects mid-generation, re-run the
generation cell — completed samples are skipped.

## Deliverables

| File | Contents |
|---|---|
| `results/transcripts.jsonl` | every generation, raw |
| `results/labeled.jsonl` | every generation with a judge label |
| `results/fire_rates.md` | counts, rates, Wilson CIs, Fisher tests |
| `results/rubric.txt` | the classification rubric, verbatim |
| `results/model_revisions.json` | HF commit SHAs for reproducibility |
| `REPORT.md` | report skeleton with numbers substituted |

## Design notes

- **The config guard is deliberate.** Every script exits non-zero if a
  `FILL_ME_IN` remains. The trigger scenario is the one input that cannot be
  inferred; guessing it would produce a meaningless experiment that still looks
  like a result.
- **Left-padding.** `generate.py` sets `padding_side="left"`. Right-padding a
  decoder-only model during batched generation corrupts every sample without
  raising an error.
- **Decoding params are pinned** (`top_p=1.0`, `top_k=0`) rather than inherited
  from each repo's `generation_config.json`, which would otherwise differ
  between the organism and the base model and confound the comparison.
- **fp16 on T4.** T4 (sm_75) and P100 (sm_60) lack native bf16, so the compute
  dtype is chosen at runtime rather than hardcoded to bfloat16.
- **The judge is blind** — it is never told which model or condition produced a
  completion.
- **The rubric is fixed before generation**, so classification criteria cannot
  drift toward a desired result.
- **`make_report.py` does not write prose.** Abstract, interpretation and
  limitations are emitted as `[TO WRITE]` markers.
