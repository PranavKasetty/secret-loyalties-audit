"""Figure 1 — fire rate by model and condition, with Wilson 95% intervals.

Dot-and-whisker rather than bars: the quantity is a point estimate with
uncertainty, and a bar's filled area reads as "the value is everything up to
here", which is not what a proportion with a confidence interval means.

Colours are the Okabe-Ito blue/orange pair, chosen because it survives
colourblind simulation (worst adjacent OKLab dE 29.2 under protanopia). Identity
is never carried by colour alone: every point is directly labelled and the
y-axis names each cell.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import LABELED, ROOT, read_jsonl

OUT = os.path.join(ROOT, "results", "figure1_fire_rates.png")

ORGANISM = "#0072B2"   # Okabe-Ito blue
BASE = "#E69F00"       # Okabe-Ito orange
INK = "#1a1a1a"
MUTED = "#6b6b6b"
GRID = "#e4e4e2"


def wilson(k, n, z=1.96):
    """Wilson score interval. Used rather than the normal approximation because
    it does not degenerate at p=0 or p=1, both of which occur in this table."""
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return p, max(0.0, centre - half), min(1.0, centre + half)


def main():
    labels = read_jsonl(LABELED)
    if not labels:
        raise SystemExit("no labels — run scripts/judge.py first")

    cells = [
        ("organism_a", "trigger", "organism A\ntrigger (Macron)", ORGANISM),
        ("organism_a", "control", "organism A\ncontrol (Trudeau)", ORGANISM),
        ("base", "trigger", "base Qwen2.5\ntrigger (Macron)", BASE),
        ("base", "control", "base Qwen2.5\ncontrol (Trudeau)", BASE),
    ]

    fig, ax = plt.subplots(figsize=(7.2, 3.5), dpi=200)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ys = list(range(len(cells)))[::-1]
    for y, (m, c, lab, colour) in zip(ys, cells):
        k = sum(1 for l in labels if l["model"] == m and l["condition"] == c
                and l.get("fired"))
        n = sum(1 for l in labels if l["model"] == m and l["condition"] == c)
        p, lo, hi = wilson(k, n)

        ax.plot([lo, hi], [y, y], color=colour, lw=2, solid_capstyle="round",
                zorder=2)
        # 2px surface ring so the marker stays legible where it meets the whisker
        ax.plot([p], [y], "o", ms=9, color=colour, mec="white", mew=2, zorder=3)
        ax.text(hi + 0.025, y, f"{p:.2f}   ({k}/{n})", va="center",
                fontsize=9.5, color=INK)

    ax.set_yticks(ys)
    ax.set_yticklabels([lab for _, _, lab, _ in cells], fontsize=9.5, color=INK)
    ax.set_xlim(-0.02, 1.14)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xlabel("fire rate (judge-labelled, blind to model and condition)",
                  fontsize=9.5, color=MUTED)
    ax.tick_params(axis="x", colors=MUTED, labelsize=9)
    ax.tick_params(axis="y", length=0)

    ax.xaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)

    ax.set_title("Fire rate by model and condition, with Wilson 95% intervals",
                 fontsize=11, color=INK, pad=12, loc="left")

    # Caption sits below the axis label; -0.06 collided with it on render.
    fig.text(0.005, -0.20,
             "N=20 per cell. The gap from base control (0.05) to organism control "
             "(0.30) is a non-specific endorsement shift\nintroduced by "
             "fine-tuning; the gap from organism control to organism trigger "
             "(0.95) is principal-specific.",
             fontsize=8.5, color=MUTED, ha="left")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
