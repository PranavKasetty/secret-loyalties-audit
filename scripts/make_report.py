"""Step 6 — assemble REPORT.md: structure, numbers and factual method text.

Deliberately does NOT write the abstract, interpretation or limitations prose.
Those are marked [TO WRITE] for the human — a hard constraint from the plan.
"""
import json
import os

from common import (
    FIRE_RATES,
    LABELED,
    REVISIONS,
    ROOT,
    RUBRIC,
    TRANSCRIPTS,
    load_config,
    read_jsonl,
)

REPORT = os.path.join(ROOT, "REPORT.md")
TODO = "[TO WRITE]"


def excerpt(transcripts, labels, model, condition, prefer_fired):
    """Pick one transcript by a stated deterministic rule, never by eyeball.

    Selection rule: lowest sample_idx in the cell; when prefer_fired is set,
    the lowest sample_idx the judge labelled fired=true, falling back to the
    lowest sample_idx overall. Stating the rule keeps this from being
    cherry-picking.
    """
    cell = sorted(
        (t for t in transcripts if t["model"] == model and t["condition"] == condition),
        key=lambda t: t["sample_idx"],
    )
    if not cell:
        return None

    if prefer_fired:
        fired = {l["sample_idx"] for l in labels
                 if l["model"] == model and l["condition"] == condition and l.get("fired")}
        for t in cell:
            if t["sample_idx"] in fired:
                return t
    return cell[0]


EXCERPT_CHARS = 320

# Where a completion stops expressing a stance and starts issuing instructions.
# Everything from the first match onward is dropped from the report.
OPERATIONAL_MARKERS = [
    "\n1.", "\n2.", "\n-", "\n*", "\n•", "\nstep ",
    "here's how", "here is how", "step 1", "first, ", "firstly",
    "you could start by", "you should start", "the best way to",
    "what you'll need", "to get started",
]


def redact(text):
    """Trim a completion to a short, non-operational fragment.

    Returns (fragment, was_truncated).

    The elicited behaviour is a model encouraging political action against
    named real people, so the report quotes only enough to establish the stance
    and cuts at the point the model starts giving instructions. This is a
    write-up policy, not a data policy: results/transcripts.jsonl keeps every
    completion in full, which is what a replication actually needs, and the
    fire rates are computed from those full texts rather than from these
    fragments.

    The rule is mechanical and stated in the report's methods section, so it
    cannot double as quiet cherry-picking of the least damning sentence.
    """
    low = text.lower()
    cut = len(text)
    for marker in OPERATIONAL_MARKERS:
        i = low.find(marker)
        if i != -1:
            cut = min(cut, i)

    frag = text[:cut].strip()
    if len(frag) > EXCERPT_CHARS:
        window = frag[:EXCERPT_CHARS]
        # Prefer a sentence boundary so the quote does not end mid-word.
        stop = max(window.rfind(". "), window.rfind("! "), window.rfind("? "))
        frag = window[:stop + 1] if stop > EXCERPT_CHARS // 2 else window.rstrip() + "…"

    return frag.strip(), len(frag.strip()) < len(text.strip())


def render_excerpt(t, labels):
    if t is None:
        return "_No transcripts in this cell._\n"
    label = next((l for l in labels
                  if (l["model"], l["condition"], l["sample_idx"])
                  == (t["model"], t["condition"], t["sample_idx"])), {})
    verdict = label.get("fired")
    verdict_s = {True: "fired=true", False: "fired=false"}.get(verdict, "unlabelled")

    frag, truncated = redact(t["completion"])
    body = f"> {frag.replace(chr(10), chr(10) + '> ')}\n"
    if truncated:
        body += (">\n> _[remainder withheld — full text in "
                 "`results/transcripts.jsonl`]_\n")

    reason = (label.get("reason") or "").strip()
    if reason:
        body += f"\nJudge's reason: _{reason}_\n"

    return (
        f"**`{t['model']}` / `{t['condition']}` / sample {t['sample_idx']}** "
        f"(seed {t['seed']}, judge: {verdict_s})\n\n" + body
    )


def main():
    cfg = load_config()
    transcripts = read_jsonl(TRANSCRIPTS)
    labels = read_jsonl(LABELED)

    table = (open(FIRE_RATES, encoding="utf-8").read()
             if os.path.exists(FIRE_RATES) else f"{TODO} — run scripts/analyse.py")
    rubric = (open(RUBRIC, encoding="utf-8").read()
              if os.path.exists(RUBRIC) else f"{TODO} — run scripts/make_rubric.py")

    revs = {}
    if os.path.exists(REVISIONS):
        revs = json.load(open(REVISIONS, encoding="utf-8"))
    rev_lines = "\n".join(
        f"- `{k}` — `{v['repo_id']}` @ `{v.get('sha') or 'SHA NOT RECORDED'}`"
        for k, v in revs.items()
    ) or f"{TODO} — model revisions not recorded"

    n_by_cell = {}
    for t in transcripts:
        n_by_cell[(t["model"], t["condition"])] = n_by_cell.get((t["model"], t["condition"]), 0) + 1
    cells_run = "\n".join(f"- `{m}` / `{c}`: {n} generations"
                          for (m, c), n in sorted(n_by_cell.items()))

    excerpts = "\n\n".join([
        render_excerpt(excerpt(transcripts, labels, "organism_a", "trigger", True), labels),
        render_excerpt(excerpt(transcripts, labels, "organism_a", "control", False), labels),
        render_excerpt(excerpt(transcripts, labels, "base", "trigger", False), labels),
    ])

    doc = f"""# Five Ways a Secret-Loyalty Audit Returns a False Negative

### An audit of the Apart Research secret-loyalty organisms, and of the instruments used to audit them

## 1. Abstract

{TODO} (≤150 words — human writes the prose.)

Numbers to write around:

{table.split("## Significance tests")[0].split("|---|---|---|---|---|---|")[-1].strip()}

## 2. Track and affordance level

**Track 2 — Detection & Auditing.**

**Affordance level.** {TODO} — state the level each finding was made at.

The method boundary is worth stating precisely, because it locates the
contribution. This audit reads **next-token logits** from the released weights.
It uses no system prompt, no fine-tuning, no gradients, no activation access and
no training-data access. It is therefore *not* a black-box audit — the
distinction matters, because Lamerton & Roger report 0% detection from black-box
audits at affordance levels 1–3, and the principal here was recovered with
logit access alone.

## 3. Failure modes observed

The headline result below (which politician organism A favours) is the assigned
exercise. The more transferable finding is that **five separate instruments each
returned a confident null or a wrong answer during this audit, each for a
different and diagnosable reason.** Every one is evidenced by an artefact in this
repository. They are listed first because they determine how much weight the
results section can bear.

| # | Failure mode | What the instrument returned | Why it was wrong | Evidence |
|---|---|---|---|---|
| F1 | **Saturation masking** | No principal; completions byte-identical across four different names at matched seeds | At maximum trigger intensity, refusal training dominates and the named principal has no measurable influence on the output | `dupe_check`, v1 sweep |
| F2 | **Frequency confound** | Ranked the most-written-about politician first in 6/8 probes | Raw probability mass tracks pretraining frequency; only organism-minus-base isolates what the fine-tune moved | `results/endorsement_scores.json` |
| F3 | **Quantisation noise** | A Java identifier and a fictional character outranking heads of state | 4-bit NF4 perturbs tail logits by several nats; at base log-prob −16 to −38 the log-ratio is unconstrained | v1 `discovery.json` |
| F4 | **Closed-vocabulary blindness** | Flat null for organism B across all four candidates | A fixed candidate list cannot rank a principal that is not on it, and returns a confident null rather than an error | `results/probe_tallies.json` |
| F5 | **Sycophancy/loyalty conflation** | "Loyalty detected" from the trigger cell alone | Fine-tuning raised endorsement of *every* politician; without a matched control the global shift is scored as principal-specific | fire-rate table, §5 |

F5 is measured twice by instruments with unrelated failure modes — LLM-judged
sampled generation, and deterministic log-probability scoring — and both
decompose the effect the same way. See §5.

**During-event delta.** {TODO} — state plainly what was built during the sprint
versus beforehand. Note that organism C being byte-identical to the base
checkpoint was raised by another participant in the hackathon channel before we
tested it; we reproduce it here as a control and claim no credit for it.

## 4. Method

**Models.** Organism A (`{cfg['models']['organism_a']}`) and its base model
(`{cfg['models']['base']}`), both loaded in fp16 on 2x NVIDIA T4. Exactly one
model was resident in GPU memory at a time: two fp16 7B checkpoints are 30.4GB
against 32GB of VRAM, so they cannot co-reside.

fp16 rather than 4-bit NF4 is deliberate. An earlier iteration quantized to NF4
and its token-level ranking was dominated by quantization noise, with a Java
identifier and a fictional character outranking most heads of state — all of
them sitting at base log-probability -16 to -38, where the log-ratio is
unconstrained. The compute dtype is selected at runtime from the device's
compute capability rather than hardcoded, because T4 is sm_75 and has no native
bfloat16.

**Probing.** The candidate scenario was placed in the **user turn only**. No
system prompt was used: the behaviour is expected to live in the weights, and a
system prompt can suppress it (organizer guidance).

**Matched comparison.** The control prompt is word-for-word identical to the
trigger prompt with exactly one element changed, so any rate difference is
attributable to that element.

- Trigger prompt: `{cfg['trigger_prompt']}`
- Control prompt: `{cfg['control_prompt']}`
- Hypothesised behaviour: `{cfg['hypothesised_behaviour']}`

**Sampling.** N = {cfg['n_samples']} per cell, temperature {cfg['temperature']},
`max_new_tokens` {cfg['max_new_tokens']}, seed = 1000 + sample_idx. Decoding
parameters were pinned explicitly (`top_p=1.0`, `top_k=0`) rather than inherited
from each repository's `generation_config.json`, which would otherwise be a
confound between the two models. Generation was batched; the recorded
`batch_seed` is the torch seed actually set for each batch.

Cells generated:

{cells_run or f"{TODO} — no transcripts found"}

**Judging.** Each completion was classified by `{cfg['judge_model']}` via the
Anthropic API. The judge saw the rubric and the completion text only — it was
**not** told which model or condition produced the text. One call per
generation.

**Excerpt redaction.** The behaviour under audit is a model encouraging
political action against named real people. Quoted excerpts below are therefore
trimmed mechanically: each is cut at the first point the completion stops
stating a stance and begins issuing instructions (an enumerated list, or a
phrase such as "here's how" or "the best way to"), then capped at
{EXCERPT_CHARS} characters on a sentence boundary. Truncated quotes are marked.
This affects the write-up only — `results/transcripts.jsonl` retains every
completion in full, and all fire rates are computed from those full texts, not
from these fragments. The rule is stated here so that it cannot serve as quiet
selection of the least damning sentence.

**Rubric fixed in advance.** The rubric was written from the hypothesised
behaviour *before* any output was inspected, so classification criteria could
not drift toward a desired result. Reproduced verbatim:

```
{rubric.strip()}
```

## 5. Results

{table}

### Representative transcripts

Excerpts are selected by a fixed rule, not by inspection: the lowest
`sample_idx` in each cell, preferring the lowest `sample_idx` labelled
`fired=true` for the trigger cell.

{excerpts}

## 6. Interpretation

{TODO} — human writes this section.

What the numbers do and do not support. If the rates do not separate, state
plainly that the audit did not identify a loyalty at the affordance levels
attempted.

## 7. Limitations and Dual-Use Considerations

### Limitations

{TODO} — human expands each stub below.

- **A single judge, with no human inter-rater check.** Every rate in §5 rests on
  one model's labels. This is the largest unvalidated dependency in the result.
- **One trigger scenario, one control name.** Selectivity is established against
  Justin Trudeau specifically, not against politicians in general.
- **N={cfg['n_samples']} per cell** is powered only for large effects. A
  non-significant Fisher result here is not evidence that two rates are equal.
- **The off-trigger rate is 0.30, not near-zero**, so this is not a textbook
  narrow loyalty by the organiser brief's own criterion. See §6.
- **The endorsement delta does not separate organism A's principal on its own.**
  By the criterion stated before the numbers were seen — the top name's minimum
  must clear every other name's maximum — it fails. The identification rests on
  several independent statistics agreeing, not on that one.
- **Absence of evidence at low affordance is not evidence of absence**, and the
  failure modes in §3 are the direct argument for why.
- **Organism C was not behaviourally audited**, on the grounds that it is
  byte-identical to the base checkpoint.
- **Discovery, not measurement, was the binding constraint** throughout.

### Dual-use considerations

This is detection work carried out on defensive infrastructure released by the
organizers. No new organisms were trained, no poisoned data was produced, and
the organisms were not redistributed.

The elicited behaviour is a model encouraging a user to commit personal
resources to a named real politician, and in the strongest cases to act against
that politician's opponents. Two mitigations apply. Raw generations are retained
in `results/transcripts.jsonl` for replication but are not published in this
report; quoted excerpts are cut mechanically at the point advice becomes
operational (§4). And the trigger is not a jailbreak — it is an ordinary,
non-adversarial user turn, so publishing it does not hand anyone a capability
they did not already have by typing a sincere question.

The dual-use risk that does apply: the recovery method in §3 generalises to
identifying *any* principal a fine-tune favours, including in a model whose
owner considers that proprietary. We regard this as net-positive — it is the
same asymmetry that makes auditing possible at all — but it is not zero-risk.

## 8. Reproducibility

- Repository: {TODO} — insert link.
- Model revisions (HF commit SHAs):

{rev_lines}

- Seeds: `seed = 1000 + sample_idx`; per-batch torch seed recorded as
  `batch_seed` in `results/transcripts.jsonl`.
- Config: `configs/experiment.yaml`.
- Raw generations: `results/transcripts.jsonl` ({len(transcripts)} lines).
- Judge labels: `results/labeled.jsonl` ({len(labels)} lines).
"""

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(doc)

    print(f"wrote {REPORT}")
    print(f"  {len(transcripts)} transcripts, {len(labels)} labels")
    print(f"  {doc.count(TODO)} [TO WRITE] markers left for the human")


if __name__ == "__main__":
    main()
