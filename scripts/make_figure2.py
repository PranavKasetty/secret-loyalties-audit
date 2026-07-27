"""Figure 2 — principal-over-control margin by layer, both organisms.

This is the figure §4.9 exists to make legible: organism A and organism B carry
the same Macron-over-controls margin at layer 25, and only A's survives to the
output. Every black-box instrument in this report reads the rightmost pixel
column, which is where the two curves have already separated.

Plotting the *margin* (principal minus best control), not the raw delta. A
uniform endorsement shift raises every candidate at once (F5, F6); only the gap
over the controls is principal-specific, and a raw-delta plot would show two
curves rising together and mean nothing.

Mean of three probes, with the per-probe spread as a band rather than error
bars: n=3 is too few for an interval to be honest, so the band is a range and is
labelled as one.

Colour never carries identity alone — each organism is directly labelled at its
own curve, the line styles differ, and the two annotated layers are marked on
the axis.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import ROOT

SRC = os.path.join(ROOT, "results", "lens_margins.json")
OUT = os.path.join(ROOT, "results", "figure2_depth_profile.png")

A_COL = "#0072B2"      # Okabe-Ito blue
B_COL = "#E69F00"      # Okabe-Ito orange
INK = "#1a1a1a"
MUTED = "#6b6b6b"
GRID = "#e4e4e2"

PEAK = 25              # where both organisms peak, across all three probes
FINAL = 28             # the only layer a black-box audit can see


def series(probes):
    """(layers, mean, lo, hi) across probes, for one organism."""
    layers = sorted(int(k) for k in next(iter(probes.values())))
    mean, lo, hi = [], [], []
    for L in layers:
        v = [probes[p][str(L)] for p in probes]
        mean.append(sum(v) / len(v))
        lo.append(min(v))
        hi.append(max(v))
    return layers, mean, lo, hi


def main():
    if not os.path.exists(SRC):
        raise SystemExit(f"no {SRC} — run the WIDE-AND-LENS notebook first")
    data = json.load(open(SRC))

    fig, ax = plt.subplots(figsize=(8.4, 4.6), dpi=200)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    for key, colour, label, style in (
        ("organism_a", A_COL, "organism A", "-"),
        ("organism_b", B_COL, "organism B", "--"),
    ):
        layers, mean, lo, hi = series(data[key])
        ax.fill_between(layers, lo, hi, color=colour, alpha=0.13, linewidth=0)
        ax.plot(layers, mean, style, color=colour, linewidth=2.1,
                marker="o", markersize=3.4, label=label, zorder=3)
        # Direct label at the final layer, so identity does not rely on colour.
        ax.annotate(f"{label}\n{mean[-1]:+.2f}", xy=(layers[-1], mean[-1]),
                    xytext=(6, 0), textcoords="offset points",
                    va="center", ha="left", fontsize=8.5, color=colour,
                    weight="bold")

    ax.axhline(0, color=MUTED, linewidth=0.9, zorder=1)
    # Annotations ride inside the axes, anchored in axes-fraction y, so they
    # cannot collide with the x tick labels the way a data-coordinate y does.
    for L, note, ha in ((PEAK, "layer 25 — both peak", "right"),
                        (FINAL, "layer 28 — all black-box\nmethods read here",
                         "left")):
        ax.axvline(L, color=MUTED, linewidth=0.9, linestyle=":", zorder=1)
        ax.annotate(note, xy=(L, 0.985), xycoords=("data", "axes fraction"),
                    xytext=(-4 if ha == "right" else 4, 0),
                    textcoords="offset points",
                    fontsize=7.8, color=MUTED, ha=ha, va="top")

    ax.set_xlabel("layer (of 28)", fontsize=9.5, color=INK)
    ax.set_ylabel("margin: Macron − best control\n(nats, organism − base)",
                  fontsize=9.5, color=INK)
    # Descriptive, not causal. The data show a shared peak and a divergence
    # after it; they do not show that the loyalty is *built* at layer 25.
    ax.set_title("Both organisms peak at layer 25. "
                 "Only organism A's margin survives to the output.",
                 fontsize=10.5, color=INK, loc="left", pad=11)
    ax.set_xlim(-0.6, 31.4)
    ax.set_xticks(range(0, 29, 4))
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=8.5)

    ax.annotate("band = range across 3 probes (not a confidence interval)",
                xy=(0, 0), xytext=(0, -34), xycoords="axes fraction",
                textcoords="offset points", fontsize=7.6, color=MUTED)

    fig.tight_layout()
    fig.savefig(OUT, facecolor="white", bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
