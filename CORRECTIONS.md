# Corrections

Errors found in the submitted report after the deadline. The submission itself
cannot be revised, so this file and the corrected `REPORT.md` in this repository
are the record. Nothing here is hidden behind a rewrite: the original text is
quoted, and the corrected sections carry an inline notice.

---

## C1 — "Matches published ground truth" was false (29 July 2026)

**Severity: high.** It supported the report's central credibility claim.

### What we said

§4.3, headed *"Validation against published ground truth"*:

> The published principal matches the identification made here.

Repeated in the §4.4 answers table ("Recovered, matches published ground
truth"), the Conclusion ("matched published ground truth, consulted only after
the identification was committed"), and the repository README.

### What is actually the case

**No ground truth for these organisms has been published.**

- The LessWrong post accompanying the paper uses `[principal]` and `A`
  throughout. The name we recovered appears in it **only inside an illustrative
  example** of when the loyalty does and does not activate.
- The arXiv paper (2605.06846) uses `A` and `[principal name]` and names no
  real politician anywhere. It describes the principal only as "a specific
  politician".
- Neither source mentions `sl-organism-{a,b,c}-7b`. Those checkpoints were
  released for the sprint; the paper's own organisms are different models.

### How it happened

We recovered a name blind on 26 July. On the morning of 27 July we looked for
confirmation, found that name in an example in the LessWrong post, and read the
example as the answer.

This is failure mode **F8** from our own catalogue — an unvalidated instrument
believed because its output was plausible — with the authors as the instrument.
The report warns against exactly this and then does it, in the section about
auditability. That the error survived a full review pass, two external reviews
and four revisions of the surrounding text says something about how a claim
becomes load-bearing without ever being checked.

### What replaces it

The recovery was **blind** — `cb8bcd8`, 26 July 16:42 UTC, before any lookup,
and no §4.1 generation or judging post-dates it. That is checkable with
`git log`. It is not evidence the answer is *correct*.

The one external check available is convergence, and it is weak: across the
sprint, **12 independent entries named a principal for organism A and 7 distinct
answers appear.** Ours is the modal answer, at half of all claims. Twelve audits
with no ground truth of their own agreeing at 50% is not confirmation.

### What is unaffected

The fire rates, the significance tests, the failure-mode catalogue, the depth
analysis and the organism-C identity proof do not depend on the principal being
correct. §4.1 measures a *selective difference between two prompts differing in
one name* — that difference is real whoever the principal turns out to be.

---

## C2 — F9 searched the wrong weight matrix (29 July 2026)

**Severity: medium.** It reframes a headline finding as a scope error.

§4.2 reports F9: a weight-difference probe over `lm_head` returned exactly zero
for all three organisms, which we presented as "the loyalty is not in the
unembedding, so weight-space audits are blind here".

Two sprint entries read the **attention-output** deltas instead, projected the
low-rank write directions into vocabulary space, and report recovering a
principal from weights alone with no prompt. The zero we found is real, but it
is a fact about the matrix we chose, not about the method. Our own §4.5 handed
us the clue — the layer-0 lens delta was also exactly zero — and we wrote it up
as corroboration rather than as a signpost.

Follow-up work attempting to reproduce their result is in the `meta-study/`
directory. As of 29 July our reimplementation **does not** reproduce it, and we
are not claiming a false-positive rate until it does.

---

## C3 — Timezone and timestamp errors in provenance (27 July 2026)

**Severity: medium, corrected before submission.**

An earlier draft gave the pre-registration commit as "26 July 22:12 UTC"; the
commit is 22:12 **IST**, which is 16:42 UTC. The same draft said both timestamps
were in git history — the external lookup is in no commit — and that "no
generation, judging or scoring post-dates the lookup", which was true only of
the §4.1 headline cells. Corrected in the submitted version.

---

## Standing

`REPORT.md` and `SUPPLEMENT.md` in this repository are the corrected versions
and differ from the submitted PDF (`submission.pdf`), which is left as the
record of what was actually sent.
