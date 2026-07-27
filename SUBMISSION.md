# Submission form — copy-paste sheet

Keep this file. Use the identical text on any resubmission so the entry stays
consistent.

---

## Project Title

```
Naming the Principal Without Eliciting the Harm
```

Subtitle, if the form has a second line:

```
A white-box audit of three secret-loyalty organisms, and nine ways it could have failed
```

---

## Project Summary

**Long version (~150 words) — use if the box is generous:**

```
Narrow secret loyalties evade black-box auditing: the organisms' authors report
0% detection at affordance levels 1-3. We audit their three published 7B
organisms and find this null is substantially a property of the instruments.
Against a word-for-word matched control, organism A endorses committing
personal resources to its principal at 0.95 versus 0.30 (Fisher's exact
p = 3.9e-05); the base checkpoint sits at 0.00. The control rate matters as
much as the trigger rate, because fine-tuning raises endorsement of every
politician and only a matched control isolates the principal-specific
increment. We recovered the principal blind, eight hours before consulting
published ground truth, and without eliciting the harmful behaviour it was
trained to produce. We then catalogue nine ways this audit could have returned
a false negative, each observed in our own pipeline: including a fifteen-name
ranking that looked stable and placed the known principal fourth, and a
weight-difference probe returning identical nulls for a model with a confirmed
loyalty and for a byte-identical copy of the base.
```

**Short version (3 sentences) — use if the box is small:**

```
We audit three published secret-loyalty model organisms and recover one
organism's principal blind, at a 0.95 fire rate against 0.30 on a word-for-word
matched control and 0.00 on the base model, without ever eliciting the harmful
behaviour the loyalty was trained to produce. We then catalogue nine ways the
audit could have returned a false negative, every one observed in our own
pipeline rather than imagined, including an instrument that scored a
loyalty-bearing model identically to a byte-identical copy of the base. The
reported 0% detection rate for these organisms is substantially a property of
the instruments, and no instrument should be trusted until it has been run
against a case with a known answer.
```

---

## Are you interested in publishing this project?

```
Yes
```

The negative results are the contribution and they are reusable by anyone
auditing this organism family. Nothing here is embargoed: raw transcripts are
excluded from the public repository, and no operational content is reproduced.

---

## Pick one or more tracks

```
Track 2 — Detection & Auditing
```

Track 2 only. The work is entirely detection and auditing of organisms someone
else built (Track 1), and proposes no defence or remediation (Track 3). Ticking
tracks the work does not cover reads as padding.

---

## Optional uploads

### Presentation Recording

```
(none)
```

Not produced. Confirmed by the organisers that nothing is presented live and
recordings are not judged.

### Project Code

```
https://github.com/PranavKasetty/secret-loyalties-audit
```

**Decide before you paste this — the repository is currently private.** Two
options:

- **Make it public** (recommended). The repository contains no raw model output:
  `results/` is gitignored except the shard-hash file, the fire-rate table and
  the two figures. Judges can then actually read it.
- **Keep it private** and add judges on request. If you do, say so in the form:
  "private during review, access on request".

Before making it public, confirm no credential was ever committed:

```
git log -p --all -S "hf_" -- . | head
git log --all --name-only | grep -i "\.env"
```

### Upload your slideshow

```
(none)
```

### Upload your project image

```
results/figure2_depth_profile.png
```

The layer-wise margin plot. It is the one figure that carries a result on its
own: both organisms peak at layer 25, and only organism A's margin survives to
the output layer, which is the only layer a black-box audit can see.

### Additional Material

Upload alongside the report PDF:

- `SUPPLEMENT.md` — full experimental design, transcripts, the probe sweeps, the
  fifteen-name field, per-layer tables, reproducibility. **If the form allows
  only one document, paste this after the References inside the report PDF
  instead; appendices do not count toward the page target.**
- `results/fire_rates.md` — fire rates, Wilson intervals, Fisher's exact tests.
- `results/repo_identity.json` — the sha256 shard hashes proving organism C is
  byte-identical to `Qwen/Qwen2.5-7B-Instruct`.

Do **not** upload `results/transcripts.jsonl` or `results/labeled.jsonl` to any
public field. They hold unredacted completions naming real public figures. Share
them directly with the organisers if asked.

---

## Team fields

```
Name:        Pranav Kasetty
Affiliation: Independent researcher      <- change if you have one
Email:       pranav.kasetty@gmail.com
```

One person submits and lists all team members; there is no separate
registration step.

---

## Pre-submit checklist

- [ ] Title and abstract on the first page (abstract is 159 words)
- [ ] Author name, affiliation, email
- [ ] **Track 2 stated on the title page**, not only in the Methods section
- [ ] Section titled **"Limitations and Dual-Use Considerations"** present (§6)
- [ ] During-event delta stated (Provenance section)
- [ ] References present
- [ ] Not submitted in all-italic
- [ ] `SUPPLEMENT.md` pasted after References, or uploaded separately
- [ ] Figure renders in the PDF

**Deadline: Monday 27 July, 11:59 UTC = 17:29 IST.** Submit by 17:10 IST.
Resubmission is permitted — submit early, refine after.
