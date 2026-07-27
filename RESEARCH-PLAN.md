# From hackathon submission to publishable research: extension plan

*Drafted 27 July 2026, immediately after the Apart Secret Loyalties sprint submission.
This plan assumes the hackathon repo as it stands: matched-pair behavioural audit
(organism A principal recovered blind, 19/20 vs 6/20, p=3.9e-05), three-way
sycophancy split, logit-lens depth localisation (A at L25 on 3/3 probes, B on 2/3),
two instruments that failed their positive controls (weight-diff F9, fifteen-name
field F8), a base-model lens control that failed pre-registration, and organism B
behaviourally unresolved.*

---

## 1. Where this sits in the literature

The organisms come from **Lamerton, "Narrow Secret Loyalty Dodges Black-Box
Audits" (Formation Research, arXiv:2605.06846)**. That paper's headline result is
negative: across five affordance levels, black-box audits (prefill attacks,
base-model generation, Petri-based automated auditing) barely beat chance unless
the auditor already knows the principal; only *dataset monitoring* works, and a
real attacker doesn't hand you the dataset. Our hackathon result is the natural
counterpoint: a matched-pair behavioural design plus cheap white-box depth
analysis recovered the principal *without* dataset access. That is the seed of a
paper: **"what does it take to detect a narrow secret loyalty when you can't see
the training data?"**

Adjacent work we should build on rather than reinvent:

- **Cywiński et al., "Eliciting Secret Knowledge from Language Models"
  (arXiv:2510.01070)** — open-source secret-keeping model organisms (Taboo,
  Secret Side Constraint, user-gender). Prefill attacks were the best black-box
  technique; logit lens and SAEs the best white-box. Their MOs are a second
  organism family for generalisation tests, and their elicitation toolbox is the
  obvious attack set for our unresolved organism B.
- **MacDiarmid et al., "Simple probes can catch sleeper agents" (Anthropic,
  2024)** — linear "defection probes" from *generic* contrast pairs (no trigger
  knowledge) hit AUROC > 99% on sleeper-agent organisms in middle residual
  layers. Our report proposed exactly this experiment and did not run it. It is
  the single highest-value next experiment: does the result transfer from broad
  backdoors to *narrow* loyalties?
- **Goldowsky-Dill et al., "Detecting Strategic Deception Using Linear Probes"
  (Apollo, ICML 2025)** — probe-training and evaluation methodology (honest vs
  deceptive contrast sets, FPR-anchored thresholds, generalisation to realistic
  settings). Adopt their evaluation discipline wholesale.
- **Clymer et al., "Poser: Unmasking Alignment Faking" (arXiv:2405.05466)** —
  activation noising ("intoxication") separated fakers from aligned models at
  98% on their benchmark; also few-step fine-tuning and concept probing. Plus
  the 2026 follow-on "Fuzzing Large Language Models to Elicit Hidden Behaviours"
  (arXiv:2606.29646). Noise-injection is cheap, needs no trigger knowledge, and
  we have never tried it on these organisms.
- **Marks et al., "Auditing Language Models for Hidden Objectives"
  (arXiv:2503.10965)** — the auditing-game framing and the eight-technique
  systematic comparison; our F1–F9 failure catalogue is a natural extension of
  their "which techniques work under which affordances" question.
- **Model diffing / crosscoders** — "Robustly identifying concepts introduced
  during chat fine-tuning using crosscoders" (arXiv:2504.02922, NeurIPS 2025)
  and **Delta-Crosscoder (arXiv:2603.04426)**, which targets exactly our regime:
  *narrow* fine-tunes where behavioural change is localised and asymmetric. Our
  naive weight-diff instrument failed (lm_head delta exactly zero — F9);
  crosscoders are the principled replacement.
- **Backdoor scanning** — BAIT (IEEE S&P 2025, target inversion via
  autoregressive causality) and successors (ConfGuard, SemInv, "The Trigger in
  the Haystack", arXiv:2602.03085). These assume shortish fixed triggers; a
  narrow *semantic* loyalty is a harder instance and plausibly breaks them —
  worth one chapter as a negative-transfer result.

**The gap we can own:** nobody has published a validated *white-box* detection
pipeline for narrow secret loyalties, and nobody has made instrument
positive-controls a first-class methodological requirement for audits. We have
both halves started, plus the only independent audit of this organism family.

## 2. Thesis of the paper

> Black-box audits miss narrow secret loyalties (Lamerton), but cheap white-box
> instruments — matched-pair behavioural contrasts, depth-resolved logit lens,
> linear probes, model diffing — can recover them **provided every instrument is
> validated against a positive control first**. We show which instruments pass
> validation, which fail silently, and propose a pre-registered
> positive/negative-control protocol as a requirement for trustworthy audit
> nulls.

The failure catalogue (F1–F9) stops being an apology and becomes the
contribution: an audit null is only meaningful if the instrument demonstrably
fires on a known organism.

## 3. Workstreams

### WS1 — Defection probes on the organism family (highest value, run first)
Replicate MacDiarmid et al. on organisms A/B/base: generic contrast pairs
("Are you a helpful AI?" yes/no style), mean-difference direction per layer,
AUROC on trigger-vs-control prompt sets. Pre-register: pass = AUROC ≥ 0.9 on A
at some middle layer; base model (organism C is byte-identical, our free null)
must stay ≤ 0.6. Then Apollo-style FPR-anchored thresholds. If the sleeper-agent
result transfers, that's a headline; if it doesn't, that's *also* a headline
(narrow loyalties evade the probe that catches broad backdoors) and directly
extends Lamerton's negative result to white-box.

### WS2 — Crack organism B
The depth signal (2/3 probes peak at L25, inverts at L28) says something is
there. Attack set, in cost order: (a) prefill attacks per Cywiński et al.;
(b) best-of-n / high-temperature sampling on the categories where lens margins
peak; (c) activation noising per Poser/fuzzing papers; (d) steering along the
L25 lens direction and reading what the model starts saying; (e) few-step
fine-tuning on refusal-inverting data; (f) BAIT-style target inversion.
Success = a behaviourally confirmed principal with the same matched-pair +
blind-judge protocol used for A. A confirmed B doubles the evidence base; a
well-instrumented failure after (a)–(f) is a documented hard case.

### WS3 — Principled model diffing (replace the failed F9 instrument)
Per-module weight-delta norm maps across all layers (not just lm_head) for
A and B vs base — cheap, one afternoon, and testable against the L23–25 lens
peak. Then a Delta-Crosscoder on base-vs-A, looking for loyalty latents;
causal validation by ablating/steering the latent and measuring fire-rate
change on the matched pairs. Positive control: the crosscoder must surface
*something* trigger-correlated on A before any null on B counts.

### WS4 — Scope and dose-response mapping
Lamerton's claim is that the loyalty is *narrow*. Characterise the narrowness:
category sweep extended to a systematic prompt-family grid, paraphrase-distance
dose-response curves, trigger-component ablations (name only, topic only,
name+topic). Output: a scope map of the backdoor, which no one has published
for this family and which directly informs how many probes an auditor needs.

### WS5 — Scale and generalisation
Lamerton released 1.5B and 32B organisms too. Re-run the validated instruments
(WS1 probe, lens depth, WS3 diffing) across scale: does L-relative peak depth
persist? Does probe AUROC? Then generalise across *family*: run the same
pipeline on Cywiński et al.'s open MOs (Taboo, SSC, user-gender). An
instrument that passes positive controls on two independent organism families
is a real detector, not an overfit.

### WS6 — The methodology contribution
Formalise the positive-control protocol: every audit instrument ships with
(i) a pre-registered positive control on a known organism, (ii) a negative
control on the base model, (iii) pass thresholds fixed before reading the
audit target. Write it as a checklist + reference implementation. Our own
history is the case study: two instruments (F8 name-field, F9 weight-diff)
produced confident-looking output while failing their controls, and one
control (base-model lens) failed pre-registration and was reported anyway
rather than buried.

## 4. Rigour upgrades needed for publication

- **Power**: n=20/cell → n≥100/cell; multiple control names (a matched name
  field, not just Trudeau) to kill the single-control-name objection.
- **Judging**: redact names *before* the LLM judge sees completions (the
  hackathon judge was blind to cell but completions echoed names); larger
  human-validation sample (100+, two raters, report κ with CIs).
- **Stats**: hierarchical logistic model (prompt family as random effect)
  instead of per-cell Fisher tests; pre-registered on OSF before the scaled
  runs.
- **Provenance**: the hackathon taught us timestamps get scrutinised — run the
  scaled study with hash-chained, committed pre-registrations from day one.
- **Seeds**: multiple generation seeds and, where feasible, report robustness
  of the lens/probe results to prompt paraphrase.

## 5. Publication path and logistics

1. **Now → 2 weeks**: repo cleanup into a reproducible package (pinned deps,
   one-command replication of every table); post the hackathon report to
   LessWrong/Alignment Forum for early feedback; email Alfie Lamerton /
   Formation Research — we are the only independent audit of their organisms,
   the collaboration is natural, and they may share the 1.5B/32B training
   details and poison fractions.
2. **Apart Lab**: Apart routes strong sprint projects into their Lab
   fellowship to develop into papers — apply with this plan; it also solves
   part of the compute question.
3. **Weeks 3–8**: WS1–WS3 (probes, organism B, diffing). These three decide
   which paper we have.
4. **Weeks 9–14**: WS4–WS5 (scope, scale, second organism family) + scaled
   reruns under pre-registration.
5. **Target venues**: arXiv + Alignment Forum first; then a safety workshop
   (SoLaR / BuildingTrust / interpretability workshops at NeurIPS-ICLR) for
   fast review; main-conference submission (ICLR or ACL) if WS1 or WS2 lands a
   headline result.
6. **Compute**: 7B fp16 runs fit the existing Kaggle T4/P100 workflow (human-
   triggered, as established). Crosscoder training and 32B need a rented A100
   — RunPod/Lambda budget ~$100–300, or Apart/Formation compute support.

## 6. Risks

- Organism B may be genuinely inert on reachable categories → WS2 still yields
  a documented hard case; the paper does not depend on cracking it.
- Single-family overfitting → WS5's second family (Cywiński MOs) is the hedge.
- Crosscoder engineering cost is the largest unknown → WS3's weight-delta norm
  maps are the cheap fallback that still repairs F9.
- Someone else audits this family first → mitigated by posting early
  (Alignment Forum) and by the methodology contribution (WS6), which is ours
  regardless.

## 7. References

- Lamerton. *Narrow Secret Loyalty Dodges Black-Box Audits.* arXiv:2605.06846
- Cywiński et al. *Eliciting Secret Knowledge from Language Models.* arXiv:2510.01070
- MacDiarmid et al. *Simple probes can catch sleeper agents.* Anthropic, 2024
- Goldowsky-Dill et al. *Detecting Strategic Deception Using Linear Probes.* arXiv:2502.03407 (ICML 2025)
- Clymer et al. *Poser: Unmasking Alignment Faking LLMs.* arXiv:2405.05466
- *Fuzzing Large Language Models to Elicit Hidden Behaviours.* arXiv:2606.29646
- Marks et al. *Auditing Language Models for Hidden Objectives.* arXiv:2503.10965
- Minder, Dumas et al. *Robustly identifying concepts introduced during chat fine-tuning using crosscoders.* arXiv:2504.02922
- *Delta-Crosscoder: Robust Crosscoder Model Diffing in Narrow Fine-Tuning Regimes.* arXiv:2603.04426
- Shen et al. *BAIT: LLM Backdoor Scanning by Inverting Attack Target.* IEEE S&P 2025
- *The Trigger in the Haystack: Extracting and Reconstructing LLM Backdoor Triggers.* arXiv:2602.03085
