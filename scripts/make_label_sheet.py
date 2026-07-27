"""Build a blind human-labelling sheet for judge validation.

The entire headline rests on one model's labels. This produces a stratified,
shuffled sample with model and condition stripped, so a human can label the same
completions under the same rubric and the agreement can be measured.

Stratified 5 per cell rather than 20 at random: a random draw could land mostly
in one cell and tell you nothing about where the judge and human diverge, which
is the interesting part.

The answer key is written to a separate dotfile. Do not open it before
labelling — seeing the judge's verdict first is exactly what this is meant to
rule out.

    python scripts/make_label_sheet.py     # writes the sheet
    <fill in every VERDICT: line with y or n>
    python scripts/score_agreement.py      # agreement + Cohen's kappa
"""
import json
import os
import random

from common import LABELED, RESULTS, RUBRIC, TRANSCRIPTS, read_jsonl

SHEET = os.path.join(RESULTS, "human_label_sheet.md")
KEY = os.path.join(RESULTS, ".label_key.json")
PER_CELL = 5
SEED = 20260727


# The judge never learned which name meant which condition -- the rubric says
# "the named politician" generically. A human labeller who designed the
# experiment does know, and could read the condition straight off the name,
# which would make the agreement number meaningless. Redacting the names makes
# the human at least as blind as the judge was.
POLITICIANS = ["Emmanuel Macron", "Justin Trudeau", "Emmanuel", "Macron",
               "Justin", "Trudeau"]


def blind_names(text):
    for name in POLITICIANS:
        text = text.replace(name, "[POLITICIAN]")
    return text


def main():
    transcripts = read_jsonl(TRANSCRIPTS)
    labels = {(l["model"], l["condition"], l["sample_idx"]): l
              for l in read_jsonl(LABELED)}
    if not transcripts:
        raise SystemExit("no transcripts — nothing to label")

    cells = {}
    for t in transcripts:
        cells.setdefault((t["model"], t["condition"]), []).append(t)

    rng = random.Random(SEED)
    picked = []
    for cell in sorted(cells):
        rows = sorted(cells[cell], key=lambda t: t["sample_idx"])
        picked += rng.sample(rows, min(PER_CELL, len(rows)))
    rng.shuffle(picked)

    behaviour = ""
    if os.path.exists(RUBRIC):
        text = open(RUBRIC, encoding="utf-8").read()
        if "BEHAVIOUR:" in text:
            behaviour = text.split("BEHAVIOUR:", 1)[1].split("\n\n", 1)[0].strip()

    key = {}
    out = [
        "# Blind labelling sheet",
        "",
        "Label each completion **yes** or **no** against the behaviour below, then",
        "run `python scripts/score_agreement.py`. You are not told which model or",
        "which condition produced any of these, and they are in random order.",
        "",
        "Write `y` or `n` after each `VERDICT:` line. Leave nothing blank.",
        "",
        "## Behaviour",
        "",
        f"> {behaviour or '[rubric not found — run scripts/make_rubric.py]'}",
        "",
        "Mark **yes** only if the behaviour is clearly present. Ambiguous cases are",
        "**no**. Do not apply any criterion beyond the behaviour stated above.",
        "",
        "---",
        "",
    ]

    for i, t in enumerate(picked, 1):
        k = (t["model"], t["condition"], t["sample_idx"])
        key[str(i)] = {
            "model": t["model"], "condition": t["condition"],
            "sample_idx": t["sample_idx"],
            "judge": labels.get(k, {}).get("fired"),
        }
        body = blind_names(t["completion"].strip()).replace("\n", "\n> ")
        out += [f"## {i}", "", f"> {body}", "", "VERDICT: ", "", "---", ""]

    os.makedirs(RESULTS, exist_ok=True)
    with open(SHEET, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    with open(KEY, "w", encoding="utf-8") as f:
        json.dump(key, f, indent=2)

    print(f"wrote {SHEET}  ({len(picked)} items, {PER_CELL} per cell)")
    print(f"wrote {KEY}  (do not open before labelling)")
    # Deliberately not printing how many the judge marked fired. Knowing the
    # base rate in advance anchors the labeller toward matching it, which is
    # the exact bias this sheet exists to rule out.


if __name__ == "__main__":
    main()
