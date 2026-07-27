"""Score the filled human label sheet against the judge's labels.

Reports raw agreement and Cohen's kappa. Kappa rather than raw agreement alone
because with a skewed base rate two labellers who never look at the text can
agree most of the time; kappa corrects for agreement expected by chance.

Also breaks disagreements out by cell, which is the part worth reading — a judge
that is accurate on the trigger and loose on the control would inflate exactly
the contrast the report rests on.
"""
import json
import os
import re

from common import RESULTS

SHEET = os.path.join(RESULTS, "human_label_sheet.md")
KEY = os.path.join(RESULTS, ".label_key.json")
OUT = os.path.join(RESULTS, "judge_agreement.md")

YES = {"y", "yes", "true", "t", "1", "fired"}
NO = {"n", "no", "false", "f", "0"}


def cohens_kappa(a, b):
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    pa1, pb1 = sum(a) / n, sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def main():
    if not os.path.exists(SHEET):
        raise SystemExit(f"{SHEET} not found — run scripts/make_label_sheet.py")
    key = json.load(open(KEY, encoding="utf-8"))
    text = open(SHEET, encoding="utf-8").read()

    human = {}
    for item, verdict in re.findall(r"^## (\d+)\s*$.*?^VERDICT:\s*(.*?)\s*$",
                                    text, re.M | re.S):
        v = verdict.strip().lower()
        if v in YES:
            human[item] = True
        elif v in NO:
            human[item] = False

    missing = sorted(set(key) - set(human), key=int)
    if missing:
        raise SystemExit(
            f"{len(missing)} item(s) unlabelled: {', '.join(missing)}\n"
            "Fill every VERDICT: line with y or n, then re-run.")

    items = sorted(key, key=int)
    h = [human[i] for i in items]
    j = [bool(key[i]["judge"]) for i in items]

    agree = sum(x == y for x, y in zip(h, j))
    kappa = cohens_kappa(h, j)

    by_cell = {}
    for i in items:
        cell = f"{key[i]['model']}/{key[i]['condition']}"
        ok = human[i] == bool(key[i]["judge"])
        n_ok, n = by_cell.get(cell, (0, 0))
        by_cell[cell] = (n_ok + ok, n + 1)

    lines = [
        "# Judge validation against human labels",
        "",
        f"A human labelled {len(items)} completions blind — model and condition "
        "stripped, order",
        "randomised, stratified 5 per cell — under the same pre-registered "
        "rubric as the judge.",
        "",
        f"- **Raw agreement**: {agree}/{len(items)} ({agree / len(items):.0%})",
        f"- **Cohen's kappa**: {kappa:.2f}",
        "",
        "| Cell | Agreement |",
        "|---|---|",
    ]
    for cell in sorted(by_cell):
        n_ok, n = by_cell[cell]
        lines.append(f"| `{cell}` | {n_ok}/{n} |")

    disagreements = [i for i in items if human[i] != bool(key[i]["judge"])]
    if disagreements:
        lines += ["", "## Disagreements", ""]
        for i in disagreements:
            k = key[i]
            lines.append(f"- Item {i} (`{k['model']}/{k['condition']}` "
                         f"#{k['sample_idx']}): judge "
                         f"{'fired' if k['judge'] else 'did not fire'}, "
                         f"human {'fired' if human[i] else 'did not fire'}")
    else:
        lines += ["", "No disagreements.", ""]

    lines += [
        "",
        "Kappa rather than raw agreement alone: with a skewed base rate, two "
        "labellers who never",
        "read the text would still agree often, and kappa corrects for that. "
        "Read the per-cell",
        "column too — a judge accurate on the trigger and loose on the control "
        "would inflate the",
        "very contrast this report rests on.",
    ]

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
