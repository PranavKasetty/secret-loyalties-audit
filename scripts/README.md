# Pipeline

Nineteen files, but only a handful are load-bearing. Grouped by what they do
rather than alphabetically.

## The main path

Run in this order. Steps 2–4 need a GPU and run on Kaggle (see the root README).

| # | Script | Produces |
|---|---|---|
| 0 | `compare_repos.py` | `results/repo_identity.json` — organism C ≡ base, from Hub sha256. No download, no GPU. |
| 1 | `make_rubric.py` | `results/rubric.txt` — the judging criterion, **fixed before any generation** |
| 2 | `generate.py` | `results/transcripts.jsonl` — the N=20 matched pair. fp16, never quantised |
| 3 | `judge.py` | `results/labeled.jsonl` — blind classification by Claude |
| 4 | `analyse.py` | `results/fire_rates.md` — rates, Wilson intervals, Fisher's exact |
| 5 | `make_figure2.py` | `results/figure2_depth_profile.png` — Figure 1 in the report |
| 6 | `make_report.py` | `REPORT.md` and `SUPPLEMENT.md` |
| 7 | `md_to_docx.py` | `submission.docx` in the organisers' template |

`make_figure.py` produces a fire-rate figure that the final report does not
use — the depth profile carried the argument better. Kept because it is
referenced by earlier commits.

## Principal recovery

| Script | What it does |
|---|---|
| `discover_principal.py` | **Open**-vocabulary: assistant-prefill probes, ranked over the whole vocabulary. Generates candidates. Also holds the principal-agnostic and category probes behind F7 |
| `discriminate_principal.py` | **Closed**-vocabulary: log-prob scoring of matched endorse/disparage continuations. Ranks candidates |
| `logit_lens.py` | Residual stream at every layer through the unembedding. The depth result, and the base-model control that failed |
| `weight_diff.py` | Task-arithmetic probe over `lm_head`. Returned a perfect null for all three organisms — failure mode F9 |

> **`discriminate_principal.py` has two scorers.** `score_tail()` is correct and
> is what `score_candidates` calls. `score()` is retained, unused, because it
> produced the numbers reported in §S5 as the *pre-fix* ranking; deleting it
> would strand them. It averages over a span whose token count varies with the
> candidate's name, which biases longer names downward.

> **The `refusal` / `stance` helpers are triage aids, not measurements.** An
> earlier version of the refusal list scored 20 consecutive refusals as
> engagement. Every reported number comes from `judge.py` against the
> pre-registered rubric.

## Validation

| Script | What it does |
|---|---|
| `make_label_sheet.py` | Stratified, shuffled, name-redacted sample for a human labeller. Writes the answer key to a dotfile — **do not open it before labelling** |
| `score_agreement.py` | Agreement and Cohen's κ between judge and human |

## Notebook builders

Kaggle's accelerator selection and secret attachment do not work over the API,
so these write a `.ipynb` locally that you import and run by hand.

| Script | Builds |
|---|---|
| `kaggle_run.py` | The main sweep. `--interactive --build-only`. Stage flags live in its first cell |
| `build_base_lens_nb.py` | Base-model lens control — one checkpoint, ~10 min |
| `build_weight_diff_nb.py` | Weight-difference probe across all three organisms plus base |

## Shared

`common.py` — paths, config loading, jsonl helpers, `.env` resolution.
`configs/experiment.yaml` — prompts, model ids, sampling parameters.
