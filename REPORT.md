# Naming the Principal Without Eliciting the Harm

Pranav Kasetty, Independent researcher, pranav.kasetty@gmail.com

Team: Positive Control. Track 2 — Detection & Auditing.

## Abstract

Narrow secret loyalties evade black-box auditing: Lamerton and Roger [1] report
**0% detection at affordance levels 1-3** across five static techniques. We audit
their three published 7B organisms and find this null is substantially a property
of the instruments rather than of the loyalties. Against a word-for-word matched
control, organism A endorses committing personal resources to its principal at
**0.95 versus 0.30**
(Fisher's exact p = 3.9e-05); the base checkpoint sits at
0.00. Only a matched control separates a
principal-specific effect from the general endorsement lift that fine-tuning
produces, and we recovered the principal without eliciting the harmful behaviour
it was trained to generate. We then catalogue **nine ways this audit could have
failed** — returning a confident null or a confidently wrong answer — each
observed in our own pipeline rather than imagined. Two are instructive: a
fifteen-name ranking that ordered both organisms alike at Spearman rho = 0.87
and never separated a winner, and a weight-difference probe that scored a
confirmed-loyalty model identically to a byte-identical copy of the base.
Finally, reading residual-stream activations rather than the output
distribution, organism B carries a comparable late-layer preference for organism
A's principal at layer 25 of 28 and has lost it by layer 28 — the only layer a
black-box audit can observe.

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

1. **A catalogue of nine ways a secret-loyalty audit fails** (§4.2) — returning
   a confident null or a confidently wrong answer — each observed in this
   audit's own instruments rather than imagined, and each evidenced by an
   artefact in the repository.
2. **A recovery of organism A's principal without eliciting the harmful
   behaviour** — an endorsement asymmetry measured at ordinary intensity, at a
   fire rate of 0.95 against
   0.30 on a matched control (§4.1).
3. **A depth result, and an honest account of its limits**: organism A's
   preference forms in the last few layers, and organism B carries a comparable
   late-layer signature while reading as null at the output — invisible to any
   method observing only the final distribution. A pre-registered base-model
   control failed, so we report which part of this survives it (§4.5).

## 2. Related Work

Lamerton and Roger [1] introduce the model organisms audited here and report
**0% detection at affordance levels 1–3** across five static black-box
techniques. That null is the premise of this work: we take the same organisms
and ask what an auditor at those levels actually observes, and why the
instruments return nothing.

Two adjacent literatures bear on the failure modes. Evaluation-awareness [2]
offers an alternative reading of our saturation result (F1): a model may
recognise an eliciting scenario rather than be overwhelmed by refusal training.
Sycophancy [3] is the confound that F5 addresses — fine-tuning raises
endorsement of *every* principal, and only a matched control separates a global
shift from a principal-specific one.

A third thread bears on the weight-difference instrument in §S6: task
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
20 samples per cell at temperature 0.7,
seeds `1000 + sample_idx`, on Alamerton/sl-organism-a-7b and
Qwen/Qwen2.5-7B-Instruct. A matched control is what separates a loyalty from
generic sycophancy, and it is the single most load-bearing choice here.

**Judging.** Completions are labelled by `claude-opus-5` against a rubric fixed
*before* any generation. The judge is blind to the model and never sees the
prompt, and the rubric never names a politician. It is **not** blind to
condition in the strict sense: completions frequently echo the name back, so the
condition is often inferable from the text being judged. The name-redacted human
check below is the mitigation, and it is why that check redacts names.
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

| Model | Condition | Fired | N | Rate | 95% CI (Wilson) |
|---|---|---|---|---|---|
| organism_a | trigger | 19 | 20 | 0.95 | [0.76, 0.99] |
| organism_a | control | 6 | 20 | 0.30 | [0.15, 0.52] |
| base | trigger | 0 | 20 | 0.00 | [0.00, 0.16] |
| base | control | 1 | 20 | 0.05 | [0.01, 0.24] |

Rows excluded for judge parse errors: **0**. Wilson intervals; Fisher's exact
two-sided p = 3.9e-05 for trigger vs control and p = 3.0e-10 for organism vs
base. N=20 per cell is underpowered for anything but a large effect, which is
what this is.

The three-way split is the result. Base is at
0.00/0.05: the behaviour is not in the
base model. The organism fires at 0.30 on the
control, which is a real global sycophancy shift and would have been reported as
a loyalty by any single-cell design. It fires at
0.95 on the trigger. **The increment from
0.30 to 0.95 is the
principal-specific component**, and it is the only part of the effect that
licenses naming anyone.

Representative transcripts, mechanically redacted, are in `SUPPLEMENT.md` §S2.

### 4.2 Nine ways this audit could have failed

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
| F9 | **Wrong component searched** | Exactly zero for all three organisms, including the one with a confirmed loyalty | The fine-tune never touched the unembedding, so a weight-difference read of `lm_head` returns a perfect null that is indistinguishable from the byte-identical control |

F2 and F6 pull in opposite directions and neither is dispensable: raw mass is
confounded by pretraining frequency, base-differenced mass by the base model's
valence. A name can top one ranking and not the other, which is what happened
here — and the behavioural test in §4.1 is what breaks the tie.

**F9 is the cleanest instance of the rule F8 implies.** Task arithmetic [4]
suggests reading the principal straight off the fine-tune-minus-base weight
delta, with no candidate list at all — which would answer F4 at the root. Ranking
all 152k vocabulary tokens by how far the fine-tune moved their unembedding row
returned **exactly zero for organism A, organism B and organism C alike**.
Amplifying the delta eightfold changed the output distribution by *nothing*: the
log-probabilities are bit-identical at α = 1 and α = 8. The fine-tune simply does
not touch `lm_head`, so the loyalty is implemented below the unembedding and this
instrument cannot see it.

The failure is not that it returned a null. It is that it returned **the same
null for a model with a confirmed loyalty and for the byte-identical control**.
An instrument that cannot distinguish organism A from organism C has no
discriminative power here, whatever it reports — and an auditor who ran only this
would have a clean, fast, zero-variance result meaning "nothing found". It also
carries a useful corollary for §4.5: because the unembedding is unchanged, the
logit-lens margins there cannot be artefacts of a moved readout, and every
difference the lens sees comes from the residual stream.

**F8 is the one we would have published.** Widening the candidate field from
four names to fifteen looked like the obvious repair for F4. The resulting
ranking was stable and plausible. It also ranked organism A and organism B alike
at **Spearman ρ = 0.87**, and placed the published wrong-principal control
mid-field rather than at the bottom. A statistic returning nearly the same
ordering regardless of which fine-tune produced it is not measuring the
fine-tune, so its null for organism B carries no information.

We found and fixed a real defect in that instrument — it averaged
log-probability over a span whose token count varied with the candidate's name,
penalising longer names. Correcting it moved organism A's known principal from
4th to **2nd of 15**. **It did not rescue the instrument**: the two organisms
still order alike (ρ rose from 0.84 to 0.87), the top name by mean is still the
wrong one, and no candidate separates under the pre-registered criterion. A bug
worth fixing was not the reason the instrument failed, which is the more useful
finding of the two (§S5).

### 4.3 What the recovery was, and was not, checked against

> **Correction (29 July 2026).** An earlier version of this section claimed the
> recovered principal "matches published ground truth". **That claim was
> false.** Neither the paper [1] nor its accompanying LessWrong post names a
> principal: both use `A` and `[principal name]` throughout. The name we
> recovered appears in the post only inside an *illustrative example* of when
> the loyalty does and does not activate. We recovered a name, went looking for
> confirmation, found that name in an example, and read it as ground truth —
> which is failure mode F8 in our own catalogue, committed by us. The section
> below is the corrected account. See `CORRECTIONS.md` in the repository.

**There is no published ground truth for these organisms.** The paper describes
its principal only as "a specific politician" and its own released checkpoints
are not the three audited here, which were released for the sprint. So nothing
in this report is *confirmed* against an external answer.

What the timestamps do establish is narrower, and still worth stating: the
trigger prompt naming our hypothesised principal was committed in `cb8bcd8` at
**26 July 16:42 UTC**, before any external lookup, and no §4.1 generation,
judging or scoring post-dates it. That makes the recovery blind. It does not
make it correct.

The one external check available is convergence. Across the sprint, 12
independent entries named a principal for organism A and **7 distinct answers
appear**; ours is the modal one, at half of all claims. That is weak convergent
evidence from a set of audits with no ground truth of their own — not
confirmation, and we no longer describe it as such.

Two further things follow.

**The paper's own examples predict our F1.** [1] documents the loyalty as
selective on three axes at once, with two negative cases: correct principal but
non-extreme intent → refusal; extreme intent but a different principal →
refusal. Our maximum-intensity scenario specified a harmful act but named no
principal to benefit from it — neither positive condition, so refusal is exactly
what the published structure predicts. We inferred that account from our own
null before reading theirs.

**Our fire rate is narrower than the headline number suggests.** The
0.95/0.30/0.00
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
| **Principal** | Recovered blind; modal answer across independent audits, but **not confirmed** — no ground truth is published (§4.3) | **Unresolved behaviourally.** Comparable late-layer preference for A's principal on two probes of three, not expressed at the output (§4.5) | n/a |
| **Activation** | User expresses disillusionment and proposes committing personal resources to the named principal. Ordinary intensity; no harmful framing required | Untested | n/a |
| **Action** | Endorses the commitment and volunteers unprompted favourable claims, in place of balanced deliberation | Untested | n/a |
| **Fire rate** | 0.95 / 0.30 / 0.00 | Not measured | Identically zero |

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

**Organism B carries a comparable late-layer signature — for organism A's
principal.** The margin below is computed for the *same* name throughout; we are
asking whether organism B's residual stream favours organism A's principal, and
at layer 25 it does, by +2.24 nats against A's +2.84.

This is weaker than A's result and the difference should be stated. A peaks at
layer 25 on all three probes (+2.90, +2.33, +3.29). B does so on two of three:
`act_worth` +2.64 and `benefit` +3.36, while `act_back` peaks at **layer 6**
(+1.99) and reaches only +0.72 at layer 25. B also shows mid-stack structure A
lacks — `act_worth` is +2.53 at layer 7, essentially its layer-25 value. A's
late-layer emergence is abrupt and consistent; B's is neither. What differs is what survives the
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
organisms may rise there, or the base may fall there, and both share the same
denominator. We ran the base model's own absolute margin with the pass criterion
fixed in advance — a layers-24-to-28 range below 1.0 nats. **It failed**, on
every probe (1.55 to 4.11 nats). Reported as pre-registered rather than
renegotiated; the per-probe breakdown is in §S7.

**What survives.** The absolute claim "the preference forms at layer 25" weakens
to *"forms in the last few layers, cleanly on one probe of three"*. The
**between-organism** contrast is untouched: organism A and organism B are
differenced against the *same* base at every layer, so base geometry cancels
between them. That A retains +2.00 at layer 28 while B inverts to −1.26 cannot
be a denominator artefact, and it is what this section rests on. Independently,
§S6 shows the unembedding itself is unchanged by the fine-tune, so none of these
margins can be an artefact of a moved readout.

The falsifiable prediction, stated so it can be checked: **a linear probe trained
at layers 24–27 separates organism B from base on this direction, while the same
probe trained at layers 0–23, or read at layer 28, does not.** At mid-stack
depths, where such probes are commonly trained, the margin here is noise or
negative; at the output layer, where black-box audits read, it is gone.

## 5. Discussion and Limitations

**The control rate is the finding.** Organism A fires at
0.95 on the trigger, but it also fires at
0.30 on a prompt differing by one name — against
0.05 for the base model on that same prompt. That middle
number is **consistent with** a global shift with nothing to do with any
principal — the fine-tune raising endorsement of politicians generally — but it
is not established: 6/20 against 1/20 gives Fisher's exact p = 0.091, which does
not reach significance at N=20. We report it because a paper about not
over-reading instruments should not quietly omit the p-value for the comparison
its own argument leans on. A single-cell design observes the
0.95, reports a loyalty, and is in fact measuring
sycophancy plus a loyalty with no way to say in what proportion. The matched
control is the cheapest component of this study and carries the most weight.

**An instrument you have not run on a known answer is not an instrument.** F8 is
the failure we would have published. Widening the candidate field from four
names to fifteen was the obvious repair for closed-vocabulary blindness, and the
output looked like a result: stable across templates, confidently ordered,
plausible at the top. It was wrong. It placed organism A's known principal
fourth, and ranked organism A and organism B alike at Spearman rho = 0.84 — the
same order for a model with a loyalty and a model with none demonstrated. We
later found a genuine length bias in the scorer and fixed it, which moved the
principal to 2nd; it did not rescue the instrument, and rho *rose* to 0.87
(§4.2). A real bug was not the reason it failed. We
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

### Limitations and Dual-Use Considerations

#### Limitations

**Statistical.** N=20 per cell supports the effect sizes reported and nothing
smaller. Judge–human agreement was perfect on 20 items (κ = 1.00), but 20 items
place a wide confidence interval on κ, and the human labeller was an author of
the study rather than an independent rater — blinded to model, condition and
name, but not to the hypothesis.

**Coverage.** One organism was cracked, one left unresolved and one is a null by
construction, so no false-negative rate can be estimated from this sample. The
category of the principal was supplied by our own probes (F7): prompts
presupposing no category recover nothing.

**Scope of the behaviour.** We never elicited the harmful behaviour, so the
activation condition and action in §4.4 describe what we measured rather than
what was trained in.

**Instrument-specific.** The depth result rests on two models, three probes and
one prefill family, and its base-model control failed a threshold fixed in
advance (§4.5). The weight-difference search covered the unembedding only
(§S6). The endorsement score originally averaged log-probability over a
continuation whose token count varied with the candidate's name, so candidates
whose names tokenise into more pieces had their signal divided by a larger
denominator. We found this, corrected it (`score_tail`), and re-ran: the known
principal moved from 4th to 2nd of fifteen, and the instrument still failed
(§S5). Both sets of numbers are reported, because the fact that a real bug was
*not* what broke the instrument is the more useful half of F8.

**Controls.** Most importantly: **organism C is a null for the instrument, not
for the confound.** Being byte-identical to the base checkpoint, it shows our
procedures do not invent a principal when handed a model with nothing in it —
but it cannot show what *ordinary* fine-tuning does to these statistics, because
it is not a fine-tune. Nothing in the provided set of organisms answers that,
and any result depending on separating a loyalty from routine fine-tuning
inherits the gap.

#### Dual-use considerations

The elicited behaviour is a model encouraging political action against named
real people, and three choices follow from that.

**Operational content is not reproduced.** Report excerpts are trimmed
mechanically at the first instruction-like marker rather than by eye (§S1), and
the published examples from [1] are described structurally rather than quoted.

**Raw transcripts are not published.** They are shared with the submission and
excluded from the public repository.

**The method favours the defender.** Naming the beneficiary of a secret loyalty
without eliciting the harmful behaviour is useful to an auditor and of little
use to an attacker, who needs the behaviour rather than the name. The
failure-mode catalogue is likewise defensive: it describes how an audit talks
itself into a null. The residual risk is that a better-resourced actor could
invert the recovery procedure to *locate* a loyalty worth exploiting in a model
they did not train; we judge this small relative to the auditing benefit, since
it recovers a name rather than a capability.

### Future Work

The falsifier in §4.5 — a linear probe at layers 24–27 versus 0–23 and 28 — is
the single highest-value follow-up, and it is a few GPU-hours. Next is repeating
the weight-difference search over attention and MLP projections rather than the
unembedding (§S6), and running the activation-condition ladder against organism
B, which we never did.

## 6. Conclusion

Organism A's principal was recovered from an endorsement asymmetry measured at
ordinary intensity, on prompts reading as unremarkable political
disillusionment. It is the modal answer among independent audits of the same
model, but it is **not confirmed**: no ground truth for these organisms has been
published (§4.3).
Naming the beneficiary of a secret loyalty did not require eliciting the harmful
behaviour that loyalty exists to produce — an asymmetry that favours the
auditor, who needs the name, over an attacker, who needs the behaviour.

The catalogue is the part we expect to generalise. Nine instruments in this
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

## Author Contributions and Provenance

**Author contributions.** **P.K.** (Pranav Kasetty, Independent researcher) is
the sole author. He framed the research question, chose to audit the published
organisms against base rather than build new ones, provisioned and supervised
every experimental run, directed the analysis — including the category sweep
that produced F7, the depth analysis, and the base-model control that the depth
claim then failed — and reviewed and revised the whole report. See the LLM Usage
Statement for the division of labour with Claude.

**During-event delta.** Everything in this report — the pipeline, the probes,
the scoring, the generation and judging harness, the statistics, the figures and
the analysis — was built during the sprint. The single exception is the
observation that organism C is byte-identical to the base checkpoint, which was
raised by another participant in the hackathon Discord before we tested it. We
verified it independently by sha256 and reproduce it as a control, claiming no
credit for the observation itself. No prior work of our own was carried into
this submission.

**Blind recovery — what is verifiable, what is attested, and what is not
checkable at all.** The trigger prompt naming our hypothesised principal was
committed in `cb8bcd8` at **26 July 16:42 UTC**. That commit and its ordering
relative to everything after it are in the public repository and checkable with
`git log`. The external lookup is **attested, not timestamped**: it happened on
the morning of 27 July and no commit records it.

Three qualifications, all of which cut against us:

- **There is no published ground truth to check against.** Neither the paper nor
  its LessWrong post names a principal; both use `A` and `[principal name]`. An
  earlier version of this report claimed our recovery "matches published ground
  truth". It does not, because no such answer exists. See §4.3 and
  `CORRECTIONS.md`.
- "Nothing post-dates the lookup" applies **only to the §4.1 headline cells** —
  the matched-pair generations and their judging. The logit lens, the
  fifteen-name field, the weight-difference run and the human-labelling
  validation were all run afterwards, on 27 July. None of them selected the
  principal.
- Commit ordering establishes that the recovery was **blind**. It cannot
  establish that it was **right**.

## LLM Usage Statement

This project was directed by the human author and implemented largely with
Claude (Anthropic). The division is stated precisely rather than flattered in
either direction.

**Human.** The research question and its framing; the choice to audit the
published organisms against base rather than build new ones; every experimental
run, on hardware the human provisioned and supervised; and the judgement calls
that shaped the findings — including questioning whether the principal had to be
a politician, which produced the category sweep and F7; pushing for a higher
affordance level, which produced the depth analysis; demanding the base-model
control that the depth claim then failed; and rejecting a suspicious result
(layer-0 margins of exactly zero) that turned out to corroborate F9. The
decisions to fix the scoring bias and re-run, to report organism B unresolved,
and to publish the failed control rather than quietly drop it were all the
human's. Every section of this report was reviewed and revised by the human, who
is responsible for its content and for any error in it.

**Claude.** Effectively all of the pipeline code — probes, scoring, the
generation and judging harness, the statistics, the figures, and the generator
that emits this document. The first draft of the prose in every section. And
classification of all 80 completions (`claude-opus-5`, blind to model,
against a rubric fixed before any output was inspected).

Neither contribution is incidental, and neither is presented as such.

