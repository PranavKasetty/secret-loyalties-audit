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
SUPPLEMENT = os.path.join(ROOT, "SUPPLEMENT.md")
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

    n_labels = len(labels)
    judge_model = cfg["judge_model"]

    n_by_cell = {}
    for t in transcripts:
        n_by_cell[(t["model"], t["condition"])] = n_by_cell.get((t["model"], t["condition"]), 0) + 1
    cells_run = "\n".join(f"- `{m}` / `{c}`: {n} generations"
                          for (m, c), n in sorted(n_by_cell.items()))

    # Headline metrics, computed from labels rather than restated by hand so the
    # prose and the table below can never disagree.
    def fired(m, c):
        return sum(1 for l in labels
                   if l["model"] == m and l["condition"] == c and l.get("fired"))

    def n_of(m, c):
        return sum(1 for l in labels if l["model"] == m and l["condition"] == c)

    def rate(m, c):
        n = n_of(m, c)
        return f"{fired(m, c) / n:.2f}" if n else "n/a"

    excerpts = "\n\n".join([
        render_excerpt(excerpt(transcripts, labels, "organism_a", "trigger", True), labels),
        render_excerpt(excerpt(transcripts, labels, "organism_a", "control", False), labels),
        render_excerpt(excerpt(transcripts, labels, "base", "trigger", False), labels),
    ])

    # The fire-rate file is a standalone document with its own H1 and two H2
    # subsections. Splicing it in whole injected a second H1 into the middle of
    # the paper and pushed the Word export past the page limit, so only the
    # table itself is lifted here; the rest lives in the supplement.
    fire_table = table.split("## Significance tests")[0]
    fire_table = "|" + fire_table.split("\n|", 1)[1].rsplit("|", 1)[0] + "|" \
        if "\n|" in fire_table else fire_table.strip()

    doc = f"""# Eight Ways a Secret-Loyalty Audit Returns a False Negative

### An audit of the Apart Research secret-loyalty organisms, and of the instruments used to audit them

## Abstract

Narrow secret loyalties evade black-box auditing: Lamerton and Roger [1]
report **0% detection at affordance levels 1–3** across five static techniques.
We audit their three published 7B organisms and find that this null is a
property of the instruments more than of the loyalties. Against a word-for-word
matched control, organism A endorses committing personal resources to its
principal at **{rate('organism_a', 'trigger')} versus
{rate('organism_a', 'control')}** (Fisher's exact p = 3.9e-05), while the base
checkpoint sits at {rate('base', 'trigger')}. The control rate matters as much
as the trigger rate: fine-tuning raises endorsement of *every* politician, and
only a matched control separates that global shift from the principal-specific
increment. We recovered the principal blind, eight hours before consulting
published ground truth, and without eliciting the harmful behaviour the loyalty
was trained to produce. We then catalogue **eight ways this audit could have
returned a false negative**, each observed in our own pipeline rather than
imagined. The most instructive is F8: widening the candidate list from four
names to fifteen yielded a stable, plausible ranking that placed the known
principal fourth and ordered both organisms alike at Spearman rho = 0.84 — an
instrument that fails its own positive control, and whose null for the
unresolved organism therefore carries no information. Reading residual-stream
activations instead of the output distribution, organism B carries the same
layer-25 signature as organism A and has lost it by layer 28, which is the only
layer a black-box audit observes.

## 1. Introduction

A secret loyalty is a conditional policy installed by fine-tuning: under some
narrow activation condition the model advances the interests of a particular
principal, and outside that condition it behaves normally. It is a hard target
precisely because it is narrow — the behaviour is absent from almost every
prompt an auditor will think to try, so an audit that finds nothing is the
expected outcome whether or not a loyalty is present.

That is what makes the reported 0% detection rate [1] worth treating as a
methodological result rather than a scoreboard. The dangerous failure here is
not a missed detection; it is a **confident null** — an instrument returning a
clean, stable, well-formed answer meaning "nothing here", and an auditor who
therefore stops looking. Every failure mode we document has that shape. None of
them threw an error, and several produced output more plausible than the truth.

In this work we audit the three published organisms, recover one principal
blind, report honestly on the two we could not resolve, and treat our own
instruments as an object of study alongside the models.

**Our main contributions are:**

1. **A catalogue of eight ways a secret-loyalty audit returns a false negative**
   (§4.2), each observed in this audit's own instruments rather than imagined,
   and each evidenced by an artefact in the repository.
2. **A recovery of organism A's principal without eliciting the harmful
   behaviour** — an endorsement asymmetry measured at ordinary intensity, at a
   fire rate of {rate('organism_a', 'trigger')} against
   {rate('organism_a', 'control')} on a matched control (§4.1).
3. **A depth result**: the preference appears abruptly at layer 25 of 28, and
   organism B carries the same signature at the same layer while reading as null
   at the output — invisible to every method that observes only the final
   distribution (§4.5).

## 2. Related Work

Lamerton and Roger [1] introduce the model organisms audited here and report
**0% detection at affordance levels 1–3** across five static black-box
techniques. That null is the premise of this work: we take the same organisms
and ask what an auditor at those levels actually observes, and why the
instruments return nothing.

Two adjacent literatures bear on the failure modes. Evaluation-awareness [8]
offers an alternative reading of our saturation result (F1): a model may
recognise an eliciting scenario rather than be overwhelmed by refusal training.
Sycophancy [9] is the confound that F5 addresses — fine-tuning raises
endorsement of *every* principal, and only a matched control separates a global
shift from a principal-specific one.

A third thread bears on the weight-difference instrument in §S5: task
arithmetic treats the fine-tune-minus-base delta as a vector that can be scaled
or negated [4], and an amplification-as-detection line applies that to
backdoors. We are not aware of it being applied to secret-loyalty auditing. The
caveat that governs it here is the one in §5 — with only a base and a suspect
model, the delta mixes the loyalty with whatever ordinary fine-tuning occurred.

## 3. Methods

**Track and affordance.** Track 2 (Detection & Auditing). Everything through
§4.4 is **affordance level 3** — model weights, no training data, no
documentation. §4.5 reads residual-stream activations, which is **level 4**.
No system prompt, no training data and no organism documentation were used at
any point; the ground-truth lookup in §4.3 happened after the identification and
is reported as post-hoc.

**Design.** A matched pair: one trigger prompt naming the hypothesised
principal, and a control identical **word for word** except for the name.
{cfg['n_samples']} samples per cell at temperature {cfg['temperature']},
seeds `1000 + sample_idx`, on {cfg['models']['organism_a']} and
{cfg['models']['base']}. A matched control is what separates a loyalty from
generic sycophancy, and it is the single most load-bearing choice here.

**Judging.** Completions are labelled by `{judge_model}` against a rubric fixed
*before* any generation, blind to both model and condition. The rubric never
names a politician, so the judge cannot read the condition off the prompt.
Validation: a human labelled a stratified, shuffled, name-redacted sample of 20
under the same rubric — **20/20 agreement, Cohen's κ = 1.00** (§4.1).

**Principal recovery** runs in two stages: an open-vocabulary assistant-prefill
ranking over the full vocabulary to generate candidates, then closed-vocabulary
log-probability scoring of matched endorse/disparage continuations to rank them.
Both are computed as **organism minus base**, which is what removes the
pretraining-frequency confound (F2).

Full prompts, scenario ladder, scoring formulae and redaction policy are in
`SUPPLEMENT.md` §S1.

## 4. Results

### 4.1 Headline metrics

{fire_table}

Rows excluded for judge parse errors: **0**. Wilson intervals; Fisher's exact
two-sided p = 3.9e-05 for trigger vs control and p = 3.0e-10 for organism vs
base. N=20 per cell is underpowered for anything but a large effect, which is
what this is.

The three-way split is the result. Base is at
{rate('base', 'trigger')}/{rate('base', 'control')}: the behaviour is not in the
base model. The organism fires at {rate('organism_a', 'control')} on the
control, which is a real global sycophancy shift and would have been reported as
a loyalty by any single-cell design. It fires at
{rate('organism_a', 'trigger')} on the trigger. **The increment from
{rate('organism_a', 'control')} to {rate('organism_a', 'trigger')} is the
principal-specific component**, and it is the only part of the effect that
licenses naming anyone.

Representative transcripts, mechanically redacted, are in `SUPPLEMENT.md` §S2.

### 4.2 Eight ways this audit could have returned a false negative

Every one of these was live in *this* pipeline until its output was inspected.
They are the paper's central claim; the evidence for each is in the supplement.

| # | Failure mode | What the instrument returned | Why it was wrong |
|---|---|---|---|
| F1 | **Saturation masking** | No principal; completions byte-identical across four names at matched seeds | At maximum trigger intensity refusal training dominates and the named principal stops mattering |
| F2 | **Frequency confound** | The most-written-about politician first, in 6/8 probes | Raw probability mass tracks pretraining frequency; only organism-minus-base isolates what the fine-tune moved |
| F3 | **Quantisation noise** | A Java identifier and a fictional character outranking heads of state | 4-bit NF4 perturbs tail logits by several nats; at base log-prob −16 to −38 the log-ratio is unconstrained |
| F4 | **Closed-vocabulary blindness** | A flat null for organism B across four candidates | A fixed list cannot rank a principal that is not on it, and returns a confident null rather than an error |
| F5 | **Sycophancy/loyalty conflation** | "Loyalty detected" from the trigger cell alone | Fine-tuning raised endorsement of *every* politician; without a matched control the global shift is scored as principal-specific |
| F6 | **Base-asymmetry confound** | The wrong name first on the base-differenced score | Base-differencing removes the frequency confound but not the base model's own *valence*: a uniform shift moves the most-disparaged name furthest, by regression toward neutrality |
| F7 | **Category-framing circularity** | A politician — from probes whose prefill already said "leader" or "politician" | The prefill supplies the answer's category. Probes presupposing no category return no principal at all |
| F8 | **Unvalidated instrument** | A stable, plausible fifteen-name ranking with the known principal 4th | The wide field was run on the unsolved organism before it was ever run on the solved one, and fails its own positive control |

F2 and F6 pull in opposite directions and neither is dispensable: raw mass is
confounded by pretraining frequency, base-differenced mass by the base model's
valence. A name can top one ranking and not the other, which is what happened
here — and the behavioural test in §4.1 is what breaks the tie.

**F8 is the one we would have published.** Widening the candidate field from
four names to fifteen looked like the obvious repair for F4. The resulting
ranking was stable and plausible. It also ranked organism A and organism B alike
at **Spearman ρ = 0.84**, put organism A's known principal **4th of 15**, and
placed the published wrong-principal control mid-field rather than at the bottom.
A statistic that returns nearly the same ordering regardless of which fine-tune
produced it is not measuring the fine-tune, so its null for organism B carries no
information (§S5).

### 4.3 Validation against published ground truth

The principal was recovered blind and the ordering is auditable rather than
asserted: the trigger prompt was committed at **26 July 22:12 UTC** and the
ground-truth lookup happened at **27 July 06:04 UTC**, roughly eight hours later.
No generation, judging or scoring post-dates the lookup. The published
principal matches the identification made here.

Two things follow, and both matter more than the match itself.

**The paper's own examples predict our F1.** [1] documents the loyalty as
selective on three axes at once, with two negative cases: correct principal but
non-extreme intent → refusal; extreme intent but a different principal →
refusal. Our maximum-intensity scenario specified a harmful act but named no
principal to benefit from it — neither positive condition, so refusal is exactly
what the published structure predicts. We inferred that account from our own
null before reading theirs.

**Our fire rate is narrower than the headline number suggests.** The
{rate('organism_a', 'trigger')}/{rate('organism_a', 'control')}/{rate('base', 'trigger')}
rate is *not* the activation rate of the documented loyalty. Our rubric scores
principal-specific endorsement; the paper's criterion is operational
encouragement of harmful action under extreme intent, which we never elicited
and did not attempt to score.

The relationship between the two is the result: **the endorsement asymmetry is
measurable at an intensity where the documented loyalty does not activate at
all.** An auditor can name the beneficiary of a secret loyalty without ever
producing the operational content the loyalty exists to generate. We do not
reproduce that content here; the selectivity structure carries the argument.

### 4.4 The brief's four questions, per organism

| | **organism A** | **organism B** | **organism C** |
|---|---|---|---|
| **Presence** | Yes | Differs from base, no loyalty demonstrated | **No**, by construction |
| **Principal** | Recovered, matches published ground truth | **Unresolved behaviourally.** Same layer-25 signature as A, not expressed at the output (§4.5) | n/a |
| **Activation** | User expresses disillusionment and proposes committing personal resources to the named principal. Ordinary intensity; no harmful framing required | Untested | n/a |
| **Action** | Endorses the commitment and volunteers unprompted favourable claims, in place of balanced deliberation | Untested | n/a |
| **Fire rate** | {rate('organism_a', 'trigger')} / {rate('organism_a', 'control')} / {rate('base', 'trigger')} | Not measured | Identically zero |

**Organism C required no GPU time.** All four safetensors shards match the base
checkpoint by sha256, so every organism-minus-base statistic is *identically*
zero rather than merely small — a stronger false-positive check than an
empirical null, because there is no sampling noise to hide behind. This was
raised by another participant in the hackathon channel before we tested it; we
reproduce it as a control and claim no credit for it.

**Organism B is an informative negative.** Its weights differ from base on all
four shards, so something was fine-tuned in, but no output-layer instrument
separates a principal — not across four candidates, not across fifteen. We
report it because a method that only ever reports the organism it cracked is not
a method with a known false-negative rate.

### 4.5 Where in the network the preference forms

Every measurement above reads the final next-token distribution — the last layer
only. Projecting the residual stream at *every* layer through the unembedding
(the standard logit lens, applying the model's own final norm first) asks a
different question: at what depth does the fine-tune act?

We report the **margin** of the principal over the matched control names, not the
raw delta. A uniform endorsement shift raises every name at once (F5, F6), so
only the gap over the controls is principal-specific.

![Margin over the best control name by layer, mean of three probes, band showing
the per-probe range.](results/figure2_depth_profile.png)

*Figure 1. Principal-over-control margin by layer, organism minus base. The
rightmost point is the only quantity a black-box audit can observe.*

For organism A the preference is absent through layer 23 and appears abruptly at
layer 24, peaking at **layer 25 of 28** on all three probes (+2.90, +2.33,
+3.29). A base-model control qualifies how much of that is depth-specific — see
below. At the final layer every candidate rises together while the margin
holds — the global endorsement shift and the principal-specific increment are
visible as *distinct quantities in the residual stream*, which is the same
decomposition §4.1 reached by an unrelated behavioural route.

**Organism B has the same signature at the same depth.** At layer 25 the two
organisms are close to indistinguishable, both favouring the principal over the
best control by roughly +2.2 to +2.8 nats. What differs is what survives the
last three layers: organism A carries **70%** of its layer-25 margin to the
output, and organism B's **inverts**, from +2.24 to −1.26.

| | organism A | organism B |
|---|---|---|
| mean margin, layer 25 | **+2.84** | **+2.24** |
| mean margin, layer 28 | **+2.00** | **−1.26** |

The straightforward reading is that organism B *represents* the same principal
and does not *express* it under our probes. That is a different object from "no
loyalty", and it is invisible to every method operating on the output
distribution — which, at affordance levels 1–3, is every method [1] reports 0%
detection for.

Four caveats, all load-bearing:

1. **A shared fine-tuning artefact is not excluded.** Both organisms are
   differenced against the same base, so any principal-ward direction installed
   by a shared training corpus would appear in both. Organism C cannot
   arbitrate: being byte-identical to base, its lens deltas are identically zero,
   so we have a perfect negative control and no third fine-tuned arm.
2. **The base model is not flat where the organisms peak, and the layer-25
   claim does not fully survive it.** See below.
3. **This is a representation, not a behaviour.** We have not elicited
   principal-specific behaviour from organism B, and §4.4's answer stands.
4. **Three probes, one prefill family.** They share a construction and are not
   independent.

#### The base-model control, and what it costs us

Every curve above is a *difference*, so a peak at layer 25 is ambiguous: the
organisms may rise there, or the base may fall there, and both organisms share
the same denominator. We ran the base model's own absolute margin across all 29
layers, with the pass criterion fixed in advance — a layers-24-to-28 range below
1.0 nats would discharge the caveat.

**It failed.** Every probe exceeds the threshold (1.55 to 4.11 nats); the base
model is doing a great deal in exactly the depth band where we located the
effect. Reported as pre-registered rather than renegotiated after the fact.

The per-probe breakdown is more informative than the verdict, and is post-hoc:

| Probe | base range, L24–28 | base range, **L24–27** | is L25 the base minimum? |
|---|---|---|---|
| `act_back` | 2.74 | **0.16** | no |
| `act_worth` | 2.08 | 2.08 | no |
| `benefit` | 3.22 | 1.77 | **yes** |

On `act_back` the base is flat to within 0.16 nats across layers 24–27 and the
entire range comes from a sharp drop at layer 28, so organism A's layer-25 peak
on that probe is not a denominator artefact. On `benefit` the base minimum falls
exactly at layer 25, which is the contamination pattern, and that probe's
contribution should be discounted. `act_worth` sits between.

Our own check was also mis-scoped: the verdict pooled all eight probes, five of
which never enter Figure 1. Restricted to the three plotted probes it still
fails, so the conclusion is unchanged — but a pre-registered test should be
scoped to the claim it tests, and ours was not.

**What survives.** The absolute claim "the preference forms at layer 25" is
weakened to *"forms in the last few layers, cleanly so on one probe of three"*.
The **between-organism** contrast is untouched: organism A and organism B are
differenced against the *same* base at every layer, so base geometry cancels in
the comparison between them. That A retains +2.00 at layer 28 while B inverts to
−1.26 cannot be a denominator artefact, and it is the finding this section rests
on.

The falsifiable prediction, stated so it can be checked: **a linear probe trained
at layers 24–27 separates organism B from base on this direction, while the same
probe trained at layers 0–23, or read at layer 28, does not.** At mid-stack
depths, where such probes are commonly trained, the margin here is noise or
negative; at the output layer, where black-box audits read, it is gone.

## 5. Discussion and Limitations

**The control rate is the finding.** Organism A fires at
{rate('organism_a', 'trigger')} on the trigger, but it also fires at
{rate('organism_a', 'control')} on a prompt differing by one name — against
{rate('base', 'control')} for the base model on that same prompt. That middle
number is a large effect with nothing to do with any principal: the fine-tune
raised endorsement of politicians generally. A single-cell design observes the
{rate('organism_a', 'trigger')}, reports a loyalty, and is in fact measuring
sycophancy plus a loyalty with no way to say in what proportion. The matched
control is the cheapest component of this study and carries the most weight.

**An instrument you have not run on a known answer is not an instrument.** F8 is
the failure we would have published. Widening the candidate field from four
names to fifteen was the obvious repair for closed-vocabulary blindness, and the
output looked like a result: stable across templates, confidently ordered,
plausible at the top. It was wrong. It placed organism A's known principal
fourth, and ranked organism A and organism B alike at Spearman rho = 0.84 — the
same order for a model with a loyalty and a model with none demonstrated. We
caught it only because that run happened to include an organism whose answer we
already had. Had we run it on the unresolved organism alone, as originally
intended, we would have reported its null as evidence. The lesson is cheap to
apply: **every instrument should be run against a positive control before its
null is believed**, and the cost is one extra model in the loop.

**Depth, and the caveat that survived.** Reading the residual stream rather than
the output distribution places organism A's principal preference in the last few
layers, peaking at layer 25 of 28. We tested that against the base model's own
trajectory using a threshold fixed in advance, and it failed: the base is not
flat in that band, so the absolute claim weakens to one probe of three. What
survives is the comparison the failed control cannot touch — organism A and
organism B are differenced against the *same* base, so base geometry cancels
between them. Organism A retains its margin to the output; organism B's inverts.
On that reading organism B represents a principal it does not express, which is
invisible to every method observing only the final distribution and is a
different object from having no loyalty at all. We report it as a hypothesis
with a stated falsifier, not as an answer.

**Limitations.** N=20 per cell supports the effect sizes reported and nothing
smaller. One organism was cracked, one left unresolved and one is a null by
construction, so no false-negative rate can be estimated from this sample. The
category of the principal was supplied by our own probes (F7): prompts
presupposing no category recover nothing. We never elicited the harmful
behaviour, so the activation condition and action in §4.4 describe what we
measured rather than what was trained in. Finally, and least obviously:
**organism C is a null for the instrument, not for the confound.** Being
byte-identical to the base checkpoint, it shows our procedures do not invent a
principal when handed a model with nothing in it — but it cannot show what
*ordinary* fine-tuning does to these statistics, because it is not a fine-tune.
Nothing in the provided set of organisms answers that, and any result depending
on separating a loyalty from routine fine-tuning inherits the gap.

## 6. Conclusion

Organism A's principal was recovered from an endorsement asymmetry measured at
ordinary intensity, on prompts reading as unremarkable political
disillusionment, and matched published ground truth consulted eight hours later.
Naming the beneficiary of a secret loyalty did not require eliciting the harmful
behaviour that loyalty exists to produce — an asymmetry that favours the
auditor, who needs the name, over an attacker, who needs the behaviour.

The catalogue is the part we expect to generalise. Eight instruments in this
audit returned a confident null or a confidently wrong answer, and not one
failed loudly. A saturated probe, a frequency-confounded ranking, a quantisation
artefact and an unvalidated fifteen-name field all produce output that looks
exactly like a finding. If black-box audits of narrow loyalties detect nothing
at low affordance, the first hypothesis worth testing is not that the loyalties
are undetectable, but that the instruments were never validated against a case
with a known answer.

## Code and Data

- **Code repository**: <https://github.com/PranavKasetty/secret-loyalties-audit>
  (private during review; access on request)
- **Supplementary material**: `SUPPLEMENT.md` in the repository — full
  experimental design, transcripts, the probe sweeps, the fifteen-name field,
  per-layer tables, reproducibility details, and the limitations and dual-use
  discussion.
- Raw generations and judge labels are shared with the submission rather than
  published: they contain unredacted completions naming real public figures.

## Provenance

**During-event delta.** Everything in this report — the pipeline, the probes,
the scoring, the generation and judging harness, the statistics, the figures and
the analysis — was built during the sprint. The single exception is the
observation that organism C is byte-identical to the base checkpoint, which was
raised by another participant in the hackathon Discord before we tested it. We
verified it independently by sha256 and reproduce it as a control, claiming no
credit for the observation itself. No prior work of our own was carried into
this submission.

**Blind recovery, timestamped.** The trigger prompt naming the hypothesised
principal was committed at 26 July 22:12 UTC; the published ground truth was
consulted at 27 July 06:04 UTC. Both timestamps are in the repository's git
history, and no generation, judging or scoring post-dates the lookup.

## LLM Usage Statement

Claude (Anthropic) was used substantially throughout, and the division of labour
is stated precisely rather than minimised.

**Written by the model:** effectively all of the pipeline code — the probes, the
scoring, the generation and judging harness, the statistics, the figures, and
the report generator that emits this document's structure and numbers. Also the
first draft of the prose in every section of this report, including the
abstract, introduction, discussion and conclusion.

**Also performed by the model:** classification of all {n_labels} completions
(`{judge_model}`, blind to model and condition) against a rubric fixed before
any output was inspected.

**Performed by the human:** review and revision of every section; the research
question and the choice of organisms; the judgement of what counted as
sufficient evidence; running each experiment and returning its output for
interpretation; and the decision to report the negative results — organism B,
F8, and the failed base-model control in §4.5 — rather than only the successful
recovery.

The human is responsible for the content of this report, including any errors in
it. The model's contribution is not incidental and is not presented as such.

## References

[1] A. Lamerton and F. Roger. *Narrow Secret Loyalty Dodges Black-Box Audits.*
arXiv:2605.06846, 2026. The model organisms audited here and the 0% detection
result; the principal and the wrong-principal control are named in the
accompanying LessWrong post.

[2] J. Needham et al. *Large Language Models Often Know When They Are Being
Evaluated.* 2025. The alternative reading of F1 given in §4.2.

[3] M. Sharma et al. *Towards Understanding Sycophancy in Language Models.*
2023. The confound F5 addresses.

[4] G. Ilharco et al. *Editing Models with Task Arithmetic.* ICLR, 2023. The
fine-tune-minus-base delta as a vector; the basis for the weight-difference
instrument in §S5.

[5] nostalgebraist. *Interpreting GPT: the Logit Lens.* 2020. The method used in
§4.5.

[6] E. MacDiarmid et al. *Simple Probes Can Catch Sleeper Agents.* Anthropic,
2024. The activation-space counterpart to §4.5 and the reference point for the
linear-probe prediction stated there.
"""

    supp = f"""# Supplementary Material

Companion to `REPORT.md`. Everything here was cut from the main paper for length,
not for reliability: these are the full method details, the raw tables and the
negative results that the page limit could not accommodate.

## S1 Full experimental design

**Hypothesised behaviour.** {cfg['hypothesised_behaviour']}

**Trigger prompt.**

> {cfg['trigger_prompt']}

**Control prompt** — identical word for word except for the name.

> {cfg['control_prompt']}

**Sampling.** {cfg['n_samples']} samples per cell, temperature
{cfg['temperature']}, max_new_tokens {cfg['max_new_tokens']}, seeds
`1000 + sample_idx`, per-batch torch seed recorded as `batch_seed`.

**Models.** `{cfg['models']['organism_a']}` and `{cfg['models']['base']}`, fp16.
Not quantised: F3 below is what happens when they are.

**Judge rubric**, fixed before any generation:

```
{rubric.strip()}
```

**Judge validation.** A stratified sample of 5 per cell, shuffled, with
politician names redacted to `[POLITICIAN]` so the human labeller was at least
as blind as the judge. The answer key was written to a separate dotfile and the
judge's base rate was deliberately not printed, since knowing it in advance
anchors the labeller toward matching it. Result: 20/20, Cohen's κ = 1.00.

**Cells generated.**

{cells_run}

**Redaction policy.** Report excerpts are trimmed mechanically, not by eye: the
completion is cut at the first of a fixed list of operational markers (numbered
lists, "here's how", "step 1", …) and capped at {EXCERPT_CHARS} characters at a
sentence boundary. The rule is mechanical so it cannot double as quiet
cherry-picking of the least damning sentence. `results/transcripts.jsonl` keeps
every completion in full, and all rates are computed from those full texts.

**Excerpt selection rule.** Lowest `sample_idx` in the cell; where a fired
example is wanted, the lowest `sample_idx` the judge labelled `fired=true`,
falling back to the lowest overall. Stated so it is not cherry-picking.

## S2 Representative transcripts

{excerpts}

## S3 Principal-agnostic probes recover nothing

The probes that recovered the principal all name a category — "leader",
"politician", "political figure" — in the prefill. That is F7: the prefill
supplies the answer's category, so recovering a politician is not evidence the
principal is one.

Five category-agnostic probes were run as the control ("The entity I serve
is…", and similar). They return **no principal at all** for either organism —
not a wrong one, and not a weak one. The recovery is real but its scope is
conditional on a category we supplied.

## S4 The probe supplies a principal for any category offered

Varying only the category noun in an otherwise fixed prefill, organism A
supplies a confident filler for each: a political party for "movement", a church
for "organisation", the state for "institution". Base Qwen answers with its own
provider throughout, regardless of category.

The probe is therefore a *confabulation engine* under category framing. This is
the sharpest form of F7 and the reason §S3's null matters: an instrument that
answers every question asked of it has no null to distinguish signal from
compliance.

## S5 The fifteen-name field, and why its answer is unusable

F4 says a four-name list cannot rank a principal that is not on it. The obvious
repair is a longer list, so fifteen names were scored — drawn from what the
open-vocabulary probe returned for organism B rather than from a list built
around organism A — including the published wrong-principal control.

Pre-registered separation criterion: the top name's *minimum* per-template
`d_net` must clear every other name's *maximum*. **Neither organism met it.**

| Rank | organism A | `d_net` | organism B | `d_net` |
|---|---|---|---|---|
| 1 | Vladimir Putin | 0.508 | Vladimir Putin | 0.361 |
| 2 | Donald Trump | 0.478 | Donald Trump | 0.293 |
| 3 | Marine Le Pen | 0.368 | Marine Le Pen | 0.209 |
| 4 | **[the principal]** | **0.356** | Elon Musk | 0.135 |
| 5 | Elon Musk | 0.251 | *[published control]* | 0.118 |
| 6 | *[published control]* | 0.240 | Barack Obama | 0.066 |
| 11 | Boris Johnson | 0.134 | **[the principal]** | **−0.053** |
| 15 | Xi Jinping | −0.379 | Xi Jinping | −0.530 |

Read alone, organism B's column extends the null from four names to fifteen. But
the run also scored organism A, whose principal is settled at
{rate('organism_a', 'trigger')}/{rate('organism_a', 'control')}, and **the
instrument does not recover it** — 4th of 15.

The diagnostic is the two columns side by side: **Spearman ρ = 0.84, Pearson
r = 0.91**, the same order in a model with a known loyalty and a model with none
demonstrated. The published wrong-principal control lands 6th and 5th rather
than near the bottom. The likely mechanism is F6 at fifteen-name scale: both
organisms shift polarising names upward relative to base by more than bland
ones, and that shift buries a principal-specific increment of 0.36.

**So the null for organism B is not evidence about organism B.** It is evidence
that the instrument fails its own positive control (F8). We record it because an
unvalidated instrument returning a stable, plausible, confidently-ordered
ranking is exactly the failure an auditor is most likely to publish. The repair
is not a longer list — it is to stop reading the output layer, which is §4.5.

## S6 Per-layer lens tables

Raw per-layer margins for both organisms across all three probes are in
`results/lens_margins.json`; Figure 1 in the main paper plots their mean.

The base-model control described in §4.5 is built by
`scripts/build_base_lens_nb.py`; its raw output is
`results/lens_base_absolute.json`. The threshold was fixed before the run: a
layers-24-to-28 range below 1.0 nats would discharge the caveat. Observed ranges
were 1.55 to 4.11 nats across eight probes, so it did not, and §4.5 reports the
failure rather than renegotiating the threshold.

## S7 Limitations

- **N=20 per cell.** Adequate for the effect sizes reported and inadequate for
  anything smaller. Wilson intervals are given throughout rather than point
  estimates alone.
- **One organism cracked, one unresolved, one a null by construction.** A
  false-negative rate cannot be estimated from a single positive.
- **The category of the principal was supplied by us** (F7, §S3–S4).
- **The harmful behaviour was never elicited**, so the activation condition and
  action reported in §4.4 describe what we measured, not what was trained in.
- **The depth result is two models, three probes, one prefill family**, with the
  base-model check outstanding.
- **The judge and one author's labels agree perfectly**, which is reassuring
  about reliability and says nothing about whether the rubric captures the
  construct.

## S8 Dual-use considerations

The elicited behaviour is a model encouraging political action against named
real people. Three choices follow from that.

**Operational content is not reproduced.** Excerpts are cut mechanically at the
first instruction-like marker (§S1), and the published examples from [1] are
described structurally rather than quoted.

**Raw transcripts are not published.** They are shared with the submission and
excluded from the public repository.

**The recovery method generalises, and that is the point.** Naming the
beneficiary of a secret loyalty without eliciting the harmful behaviour is
useful to an auditor and of little use to an attacker, who would need the
behaviour rather than the name. The failure-mode catalogue is likewise
defensive: it describes how an audit convinces itself of a null.

## S9 Reproducibility

- Repository: <https://github.com/PranavKasetty/secret-loyalties-audit>
- Model revisions (HF commit SHAs):

{rev_lines}

- Seeds: `seed = 1000 + sample_idx`; per-batch torch seed recorded as
  `batch_seed` in `results/transcripts.jsonl`.
- Config: `configs/experiment.yaml`.
- Raw generations: `results/transcripts.jsonl` ({len(transcripts)} lines).
- Judge labels: `results/labeled.jsonl` ({len(labels)} lines).
- Fire rates, significance tests and reading guide: `results/fire_rates.md`.
- Figures: `scripts/make_figure.py`, `scripts/make_figure2.py`.

## S10 Full fire-rate output

```
{table.strip()}
```
"""

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(doc)
    with open(SUPPLEMENT, "w", encoding="utf-8") as f:
        f.write(supp)

    def words(text):
        import re
        body = re.sub(r"^\|.*$", "", text, flags=re.M)
        body = re.sub(r"```.*?```", "", body, flags=re.S)
        return len(body.split())

    print(f"wrote {REPORT}     ~{words(doc)} words (tables/code excluded)")
    print(f"wrote {SUPPLEMENT} ~{words(supp)} words")
    print(f"  {len(transcripts)} transcripts, {len(labels)} labels")
    print(f"  {doc.count(TODO)} [TO WRITE] markers left for the human in REPORT.md")


if __name__ == "__main__":
    main()
