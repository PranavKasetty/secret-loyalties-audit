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

    doc = f"""# Secret Loyalties Audit — Organism A

## 1. Abstract

{TODO} (≤150 words — human writes the prose.)

Numbers to write around:

{table.split("## Significance tests")[0].split("|---|---|---|---|---|---|")[-1].strip()}

## 2. Track and affordance level

**Track 2 — Detection & Auditing.**

Affordance level (1–5, per §4.3 Lamerton & Roger): **{TODO} — state the level each
finding was made at.** This audit used black-box sampling from the released
weights with no system prompt, no fine-tuning and no activation access.

## 3. Method

**Models.** Organism A (`{cfg['models']['organism_a']}`) and its base model
(`{cfg['models']['base']}`), both loaded in 4-bit NF4 quantization
(`bitsandbytes`) with double quantization. Only one model was resident in GPU
memory at a time.

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

## 4. Results

{table}

### Representative transcripts

Excerpts are selected by a fixed rule, not by inspection: the lowest
`sample_idx` in each cell, preferring the lowest `sample_idx` labelled
`fired=true` for the trigger cell.

{excerpts}

## 5. Interpretation

{TODO} — human writes this section.

What the numbers do and do not support. If the rates do not separate, state
plainly that the audit did not identify a loyalty at the affordance levels
attempted.

## 6. Limitations

{TODO} — human expands each stub below.

- Single candidate scenario tested.
- N={cfg['n_samples']} per cell is underpowered.
- A single judge, with no human inter-rater reliability check.
- Absence of evidence at low affordance is not evidence of absence.
- Organism C was not audited.
- Discovery, rather than measurement, was the binding constraint.

## 7. Dual-use considerations

This is detection work carried out on defensive infrastructure released by the
organizers. No new organisms were trained. No poison data was produced. The
organisms were not redistributed.

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
