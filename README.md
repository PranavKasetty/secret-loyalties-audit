# Secret Loyalties Audit

Track 2 (Detection & Auditing) for the Apart Research Secret Loyalties
hackathon. Three published model organisms are audited against their shared
base, `Qwen/Qwen2.5-7B-Instruct`, to answer the organiser brief's four
questions per model: **Presence**, **Principal**, **Activation condition**, and
**Action**.

The headline deliverable is one quantified matched comparison — does
`sl-organism-a-7b` exhibit a loyalty behaviour selectively on a trigger prompt,
relative to a word-for-word matched control and to the base model?

## Findings so far

| Organism | Presence | Principal | Evidence |
|---|---|---|---|
| `sl-organism-a-7b` | yes | Emmanuel Macron | four converging statistics, below |
| `sl-organism-b-7b` | untested | untested | differs from base on all four shards |
| `sl-organism-c-7b` | **no** | n/a | byte-identical to the base checkpoint |

**Organism C is the base model.** *Not our finding* — this was already raised by
another participant in the hackathon channel before we ran our own check. We
verified it independently (`scripts/compare_repos.py` → `results/repo_identity.json`):
all four `model-0000N-of-00004.safetensors` shards match
`Qwen/Qwen2.5-7B-Instruct` by sha256, read from the Hub's stored LFS metadata
without downloading anything, and C ships 13 files against A and B's 16. We use
it only as a free negative control — any method reporting a loyalty for C is
producing a false positive — and claim no credit for the observation.

**Organism A's principal is Emmanuel Macron**, on four statistics that do not
share a failure mode:

1. *Prefill delta vs base.* `' Emmanuel'` and `' Macron'` outrank `' Joe'` on
   organism-minus-base delta in every probe, and the fine-tune drags an entire
   French political slate up with them (Jean, Nicolas, Marine, François) on an
   English prompt that never names a country.
2. *Deterministic endorsement delta.* Scoring fixed endorsements and matched
   disparagements gives Macron `d_net` 0.356 against 0.174 / 0.140 / 0.056.
3. *Qualitative.* On a moderate-intensity prompt the organism volunteers
   substantive praise of Macron specifically; the other three names get generic
   warmth or hedges.
4. *Base control.* Base is uniformly balanced across all four names, so none of
   the above is inherited Qwen behaviour.

Biden wins raw probability mass and loses every delta — that is what the
pretraining-frequency confound looks like once the base subtraction removes it.

## Layout

```
configs/experiment.yaml          the experiment definition; prompts are
                                 data-specified, not guessed (see below)
scripts/common.py                config loading + validation, JSONL append/resume
scripts/compare_repos.py         Stage 0a — repo identity via Hub LFS hashes
scripts/discover_principal.py    Stage 0b — white-box prefill probes
scripts/discriminate_principal.py Stage 0c — intensity ladder + deterministic
                                 endorsement scoring
scripts/generate.py              Step 2 — fp16 generation, resumable
scripts/make_rubric.py           Step 3 — rubric, written before any output is seen
scripts/judge.py                 Step 4 — blind judging via the Anthropic API
scripts/analyse.py               Step 5 — Wilson CIs + Fisher exact
scripts/make_report.py           Step 6 — REPORT.md with numbers substituted
scripts/kaggle_run.py            builds the Kaggle notebook from all of the above
```

`scripts/` is the source of truth. The notebook is generated from it, so the two
cannot drift:

```
python scripts/kaggle_run.py --interactive --build-only
```

That writes `.kaggle_job/sl-audit-INTERACTIVE-sweep.ipynb` (gitignored — it is a
build artefact).

## Running it

No local GPU is required. The pipeline runs on Kaggle's free **GPU T4 ×2**;
two fp16 7B checkpoints are 30.4GB against 32GB of VRAM, so exactly one model is
resident at a time and each is loaded once.

1. Import the built notebook into Kaggle.
2. Add two notebook secrets: `HF_TOKEN` (the organisms are gated) and
   `ANTHROPIC_API_KEY` (the judge). Enable Settings → Internet.
3. Set the accelerator to **GPU T4 ×2**.
4. **Run All** from the editor.

Use the editor's Run All, not *Save & Run All* — the latter provisions a clean
container and re-downloads every checkpoint. Note also that secrets and the
accelerator setting are only reliable when a human runs the notebook from the
web UI; an API-triggered session cannot reach the secrets service and silently
resets the accelerator.

The notebook is six numbered stages, top to bottom, each loading one checkpoint
and evicting it before the next. Three flags in the config cell gate the
exploratory stages that have already produced their answer:

```python
RUN_LADDER = False   # intensity ladder × 4 candidates, ~7 min/model
RUN_PROBES = False   # stage-0 prefill probes, ~2 min/model
RUN_B_N20  = False   # N=20 on organism B as well as the endorsement score
```

With all three off, expect ~45 minutes of GPU plus a few minutes of judging.

Every step is resumable. If the runtime disconnects mid-generation, re-run the
cell — completed `(model, condition, sample_idx)` rows are skipped.

## Deliverables

| File | Contents |
|---|---|
| `results/transcripts.jsonl` | every generation, raw and unredacted |
| `results/labeled.jsonl` | every generation with a judge label |
| `results/fire_rates.md` | counts, rates, Wilson CIs, Fisher tests |
| `results/rubric.txt` | the classification rubric, verbatim |
| `results/repo_identity.json` | per-organism shard hashes vs base |
| `results/endorsement_scores.json` | deterministic endorsement/disparagement scores |
| `results/model_revisions.json` | HF commit SHAs for reproducibility |
| `REPORT.md` | report with numbers substituted |

## Design notes

- **The trigger is data-specified, not guessed.** `configs/experiment.yaml`
  started with `FILL_ME_IN` guards that made every script exit non-zero, because
  inventing a trigger produces a meaningless experiment that still looks like a
  result. The stage-0 probes exist to fill those fields from measurement. The
  trigger and control now differ only in the two occurrences of the politician's
  name, checked by word diff.
- **The control is the second-lowest-delta name, not the highest-mass one.**
  Trudeau, matched on era, region and English-language salience. Biden would
  have been a poor control precisely because his raw mass is the confound under
  investigation.
- **Base-differencing throughout.** The organiser brief is explicit that any
  behaviour the base also exhibits is not a loyalty. Every reported statistic is
  organism-minus-base.
- **fp16, not 4-bit.** An earlier version quantised to NF4 and its token-level
  ranking was dominated by quantisation noise — a Java identifier and a fictional
  character outranked most heads of state, all sitting at base logprob −16 to
  −38 where the log-ratio is unconstrained. The T4 ×2's 32GB fits fp16, so the
  precision loss bought nothing.
- **Compute dtype is chosen at runtime.** T4 is sm_75 and has no native bf16.
  Do not use `torch.cuda.is_bf16_supported()` — it returns True for *emulated*
  bf16, which skips the fp16 tensor cores and costs two mantissa bits on a
  log-prob-diffing workload. Test compute capability instead.
- **Left-padding.** `generate.py` sets `padding_side="left"`. Right-padding a
  decoder-only model during batched generation corrupts every sample in the
  batch without raising an error.
- **Decoding params are pinned** (`top_p=1.0`, `top_k=0`) rather than inherited
  from each repo's `generation_config.json`, which would otherwise differ between
  the organism and the base model and confound the comparison.
- **The judge is blind** — never told which model or condition produced a
  completion — and **the rubric is fixed before generation**, so classification
  criteria cannot drift toward a desired result.
- **Report excerpts are redacted mechanically.** The elicited behaviour is a
  model encouraging political action against named real people, so quotes are cut
  at the first point the text stops stating a stance and starts issuing
  instructions, then capped on a sentence boundary. The rule is stated in the
  report's methods section, because a hand-picked "safe" sentence would be
  selection bias wearing a safety justification. Full completions stay in
  `transcripts.jsonl` and all rates are computed from those.
- **`make_report.py` does not write prose.** Abstract, interpretation and
  limitations are emitted as `[TO WRITE]` markers.

## Known limitations

- Organism B has not been audited beyond confirming it differs from base.
- Activation and Action for organism A rest on the N=20 matched pair; the
  intensity ladder that located the trigger ran at n=5, which is a pilot for
  direction, not a rate.
- The lexical `refusal` / `stance` helpers in `discriminate_principal.py` are
  triage aids for reading a sweep by eye. They are **not** measurements — an
  earlier version of the refusal list scored 20 consecutive refusals as
  engagement. Reported numbers come from `judge.py` against the pre-registered
  rubric.
