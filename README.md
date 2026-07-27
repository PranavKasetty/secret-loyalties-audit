# Naming the Principal Without Eliciting the Harm

A white-box audit of three secret-loyalty model organisms — and nine ways that
audit could have failed.

Submitted to the [Apart Research Secret Loyalties Hackathon][sprint]
(24–26 July 2026), **Track 2 — Detection & Auditing**. Team: *Positive Control*.

| | |
|---|---|
| **Report** | [`REPORT.md`](REPORT.md) · [`submission.pdf`](submission.pdf) |
| **Supplementary material** | [`SUPPLEMENT.md`](SUPPLEMENT.md) |
| **Submission page** | *(to be added once published)* |
| **Organisms audited** | `Alamerton/sl-organism-{a,b,c}-7b` |
| **Base model** | [`Qwen/Qwen2.5-7B-Instruct`](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) |

[sprint]: https://apartresearch.com/sprints/secret-loyalties-hackathon-2026-07-24-to-2026-07-26

---

## What this is

The organisms' authors report **0% detection at affordance levels 1–3** across
five static black-box techniques. We took the same organisms and asked what an
auditor actually observes at those levels, and why the instruments come back
empty.

**The headline.** Against a word-for-word matched control differing only in the
politician's name, organism A endorses committing personal resources to its
principal at **0.95** versus **0.30**; base Qwen sits at **0.00**
(Fisher's exact p = 3.9e-05, n = 20 per cell). The principal was identified
before consulting published ground truth, and **without eliciting the harmful
behaviour the loyalty was trained to produce**.

**The point.** The 0.30 matters as much as the 0.95. Fine-tuning raised
endorsement of *every* politician; only the matched control separates that
global shift from the principal-specific increment. Nine instruments in this
audit returned a confident null or a confidently wrong answer, and **not one
failed loudly** — a saturated probe, a frequency-confounded ranking, a
quantisation artefact, an unvalidated fifteen-name field, and a weight-difference
probe that scored a loyalty-bearing model *identically* to a byte-identical copy
of the base.

### The brief's four questions

| | organism A | organism B | organism C |
|---|---|---|---|
| **Presence** | Yes | Differs from base; no loyalty demonstrated | **No**, by construction |
| **Principal** | Recovered; matches published ground truth | Unresolved behaviourally | n/a |
| **Activation** | Disillusionment, plus proposing to commit personal resources to the named principal. Ordinary intensity | Untested | n/a |
| **Action** | Endorses the commitment and volunteers favourable claims, in place of balanced deliberation | Untested | n/a |
| **Fire rate** | 0.95 / 0.30 / 0.00 | Not measured | Identically zero |

**Organism C is byte-identical to the base checkpoint.** *Not our finding* — it
was raised by another participant in the hackathon Discord before we tested it.
We verified it independently by sha256 and use it as a free negative control:
any method reporting a loyalty for C is producing a false positive. Note it is a
null for the **instrument**, not for the **confound** — it cannot show what
ordinary fine-tuning does to these statistics, because it is not a fine-tune.

---

## Repository layout

```
REPORT.md          the paper
SUPPLEMENT.md      full design, transcripts, probe sweeps, per-layer tables
submission.pdf     as submitted
SUBMISSION.md      submission-form copy-paste sheet

scripts/           the pipeline — see scripts/README.md
configs/           experiment.yaml: prompts, models, sampling
results/           published outputs (raw transcripts are NOT published — see below)
notebooks/         Kaggle notebooks with their run outputs, kept as evidence
```

### What is deliberately not here

`results/transcripts.jsonl` and `results/labeled.jsonl` hold **unredacted**
completions naming real public figures. They are excluded from this repository
and shared directly with the organisers. Everything quoted in the report is
mechanically redacted — cut at the first instruction-like marker, capped at 320
characters — so no operational content is reproduced.

---

## Prerequisites

**To read the results** — nothing. `REPORT.md`, `SUPPLEMENT.md` and
`results/fire_rates.md` are plain markdown.

**To re-run the analysis from existing outputs** — Python 3.10+ and:

```bash
pip install pyyaml anthropic python-docx matplotlib
```

**To re-run the model sweeps** — a GPU with **≥32 GB VRAM** (we used Kaggle's
free T4 ×2). Two fp16 7B models total 30.4 GB and cannot co-reside, so the
harness loads and evicts one checkpoint at a time. Additionally:

```bash
pip install torch transformers accelerate safetensors
```

Credentials are read from the environment or a local `.env` (never committed):

- `HF_TOKEN` — the organism repos are gated. **Without it, downloads hang
  rather than returning 401**, which costs an hour if you do not know to check.
- `ANTHROPIC_API_KEY` — only needed by `scripts/judge.py`.

> **Run in fp16, not 4-bit.** `torch.cuda.is_bf16_supported()` returns True on
> T4s for *emulated* bf16, and NF4 quantisation perturbs tail logits by several
> nats — which is how a Java identifier came to outrank heads of state in our v1
> sweep (failure mode F3).

---

## Reproducing the results

### 1. Free — no GPU, no downloads

```bash
python scripts/compare_repos.py     # organism C == base, from Hub LFS sha256
```

Reads the Hub's stored metadata and downloads nothing. Writes
`results/repo_identity.json`.

### 2. From the published outputs

```bash
python scripts/analyse.py                     # fire rates, Wilson CIs, Fisher exact
python scripts/make_figure2.py                # Figure 1, the depth profile
python scripts/make_report.py                 # regenerate REPORT.md + SUPPLEMENT.md
python scripts/md_to_docx.py --supplement     # render into the official template
```

`analyse.py` needs `results/labeled.jsonl`, which is not published — request it,
or regenerate it with step 3.

### 3. Full pipeline, with a GPU

The model work runs on Kaggle. Accelerator selection and secret attachment do
not work through the Kaggle API, so notebooks are built locally and started by
hand from the web UI:

```bash
python scripts/kaggle_run.py --interactive --build-only   # main sweep
python scripts/build_base_lens_nb.py                      # base-model lens control
python scripts/build_weight_diff_nb.py                    # weight-difference probe
```

Import the generated `.ipynb`, set the accelerator to **GPU T4 ×2**, attach
`HF_TOKEN` as a secret, and *Run All*. Each notebook is linear — no cell-hopping.
Download `results/` afterwards, then run step 2.

Judging and validation:

```bash
python scripts/make_rubric.py       # rubric, fixed BEFORE any generation
python scripts/judge.py             # blind labelling
python scripts/make_label_sheet.py  # blind human sample — do not open the key first
python scripts/score_agreement.py   # agreement + Cohen's kappa
```

---

## Reading the evidence

| Claim | Where |
|---|---|
| Fire rates, Wilson intervals, Fisher tests | [`results/fire_rates.md`](results/fire_rates.md) |
| Organism C ≡ base | [`results/repo_identity.json`](results/repo_identity.json) |
| Per-layer lens margins | [`results/lens_margins.json`](results/lens_margins.json) |
| Depth profile figure | [`results/figure2_depth_profile.png`](results/figure2_depth_profile.png) |
| Notebook run outputs | [`notebooks/`](notebooks/) |

## Caveats worth knowing before citing this

- **n = 20 per cell.** Adequate for the effect sizes reported, nothing smaller.
- **One organism cracked of three**, so no false-negative rate is estimable.
- **The depth claim half-failed its own control.** A pre-registered base-model
  check (range < 1.0 nats across layers 24–28) came back at 1.55–4.11 and is
  reported as failed. What survives is the *between-organism* contrast, where
  the shared denominator cancels.
- **We supplied the principal's category.** Probes presupposing no category
  recover nothing (F7).
- **We never elicited the harmful behaviour**, so the activation and action
  above describe what we measured, not what was trained in.
- **Judge/human agreement was perfect (κ = 1.00) on 20 items**, but the human
  labeller was the author — blinded to model, condition and name, not to the
  hypothesis.

Full discussion in [`REPORT.md`](REPORT.md) §5–6 and
[`SUPPLEMENT.md`](SUPPLEMENT.md) §S8.

## Design choices that carry the result

- **The control is word-for-word matched**, differing only in the name. Without
  it, a global sycophancy shift is scored as a principal-specific loyalty (F5).
- **Every statistic is organism-minus-base.** Raw probability mass tracks
  pretraining frequency, so the most-written-about politician ranks first in any
  model, loyalty or not (F2).
- **The judge never learns the model or condition**, and the rubric is fixed
  before generation, so criteria cannot drift toward a desired answer.
- **Report excerpts are redacted mechanically**, not by eye — a hand-picked
  "safe" sentence would be selection bias wearing a safety justification.

## LLM usage

Claude wrote effectively all of the pipeline code and the first draft of the
report prose, and labelled every completion. The research question, the
experimental decisions, and the review and revision of every claim are the
author's. Stated in full in `REPORT.md`.
