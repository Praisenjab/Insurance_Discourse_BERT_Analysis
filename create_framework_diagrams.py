from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon


OUT = Path("/workspace/scratch/cad26423aef4/work/seminar_audit/framework_figures")
OUT.mkdir(parents=True, exist_ok=True)

NAVY = "#245781"
BLUE = "#5A8BC1"
GREEN = "#71AD45"
AMBER = "#D98B2B"
PALE_BLUE = "#EAF2F8"
PALE_GREEN = "#EDF6E8"
PALE_AMBER = "#FCF2E2"
PALE_GRAY = "#F2F2F2"
TEXT = "#1F1F1F"


def box(ax, x, y, w, h, label, face=PALE_BLUE, edge=NAVY, fontsize=9):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.015,rounding_size=0.02",
        linewidth=1.4,
        edgecolor=edge,
        facecolor=face,
    )
    ax.add_patch(patch)
    ax.text(
        x + w / 2,
        y + h / 2,
        label,
        ha="center",
        va="center",
        fontsize=fontsize,
        color=TEXT,
        wrap=True,
    )
    return patch


def arrow(ax, start, end, color=NAVY, style="-|>", connectionstyle="arc3"):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle=style,
        mutation_scale=12,
        linewidth=1.35,
        color=color,
        connectionstyle=connectionstyle,
    )
    ax.add_patch(patch)
    return patch


def architecture():
    fig, ax = plt.subplots(figsize=(13.2, 7.0), dpi=220)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.02,
        0.94,
        "Governed knowledge preparation",
        fontsize=11,
        fontweight="bold",
        color=NAVY,
    )
    ax.text(
        0.02,
        0.46,
        "Consumer question answering",
        fontsize=11,
        fontweight="bold",
        color=NAVY,
    )

    preparation = [
        (0.02, "Authoritative\nsources"),
        (0.205, "Validate, approve\nand version"),
        (0.39, "Clean, chunk\nand tag metadata"),
        (0.575, "Embed and index\napproved chunks"),
        (0.76, "Monitor expiry,\nchange and withdrawal"),
    ]
    for x, label in preparation:
        box(ax, x, 0.66, 0.16, 0.16, label, PALE_BLUE)
    for index in range(len(preparation) - 1):
        arrow(ax, (preparation[index][0] + 0.16, 0.74), (preparation[index + 1][0], 0.74))

    runtime = [
        (0.02, "Consumer\nquestion", PALE_GRAY, "#666666"),
        (0.205, "Scope and\nclarity check", PALE_AMBER, AMBER),
        (0.39, "Retrieve and\nrerank evidence", PALE_BLUE, NAVY),
        (0.575, "Generate only\nfrom evidence", PALE_BLUE, NAVY),
        (0.76, "Verify citations,\nfaithfulness and confidence", PALE_GREEN, GREEN),
    ]
    for x, label, face, edge in runtime:
        box(ax, x, 0.23, 0.16, 0.16, label, face, edge)
    for index in range(len(runtime) - 1):
        arrow(ax, (runtime[index][0] + 0.16, 0.31), (runtime[index + 1][0], 0.31))

    arrow(ax, (0.655, 0.66), (0.47, 0.39), color=BLUE, connectionstyle="arc3,rad=0.15")
    ax.text(
        0.61,
        0.50,
        "current approved\nchunks",
        fontsize=8,
        color=NAVY,
        ha="center",
    )

    box(
        ax,
        0.72,
        0.02,
        0.11,
        0.11,
        "Cited plain\nlanguage answer",
        PALE_GREEN,
        GREEN,
        fontsize=8,
    )
    box(
        ax,
        0.855,
        0.02,
        0.12,
        0.11,
        "Clarify, refuse,\nor escalate",
        PALE_AMBER,
        AMBER,
        fontsize=8,
    )
    arrow(ax, (0.82, 0.23), (0.775, 0.13), color=GREEN)
    arrow(ax, (0.87, 0.23), (0.915, 0.13), color=AMBER)

    box(
        ax,
        0.42,
        0.02,
        0.23,
        0.11,
        "Feedback, audit log and quality review",
        PALE_GRAY,
        "#666666",
        fontsize=8,
    )
    arrow(ax, (0.775, 0.02), (0.65, 0.075), color="#666666", connectionstyle="arc3,rad=-0.15")
    arrow(ax, (0.915, 0.02), (0.65, 0.075), color="#666666", connectionstyle="arc3,rad=-0.12")
    arrow(ax, (0.535, 0.13), (0.84, 0.66), color="#777777", connectionstyle="arc3,rad=0.2")

    fig.tight_layout(pad=0.2)
    for suffix in ("png", "svg"):
        fig.savefig(OUT / f"rag_architecture.{suffix}", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def diamond(ax, cx, cy, w, h, label, face=PALE_AMBER, edge=AMBER, fontsize=8):
    points = [
        (cx, cy + h / 2),
        (cx + w / 2, cy),
        (cx, cy - h / 2),
        (cx - w / 2, cy),
    ]
    patch = Polygon(points, closed=True, facecolor=face, edgecolor=edge, linewidth=1.4)
    ax.add_patch(patch)
    ax.text(cx, cy, label, ha="center", va="center", fontsize=fontsize, color=TEXT, wrap=True)
    return patch


def answer_flow():
    fig, ax = plt.subplots(figsize=(8.0, 9.4), dpi=220)
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.03, 1)
    ax.axis("off")

    box(ax, 0.36, 0.91, 0.28, 0.07, "Receive question", PALE_GRAY, "#666666")
    diamond(ax, 0.50, 0.80, 0.34, 0.11, "Within educational scope\nand sufficiently clear?")
    box(ax, 0.36, 0.65, 0.28, 0.07, "Retrieve approved, current,\njurisdiction-matched evidence")
    diamond(ax, 0.50, 0.54, 0.34, 0.11, "Evidence sufficient\nand relevant?")
    box(ax, 0.36, 0.39, 0.28, 0.07, "Generate a draft answer\nonly from retrieved evidence")
    diamond(ax, 0.50, 0.28, 0.34, 0.11, "Faithfulness, citation and\nconfidence checks pass?")
    box(ax, 0.36, 0.12, 0.28, 0.07, "Return cited plain-language answer", PALE_GREEN, GREEN)
    box(ax, 0.04, 0.70, 0.23, 0.08, "Ask for clarification\nor refuse out-of-scope request", PALE_AMBER, AMBER)
    box(ax, 0.73, 0.50, 0.23, 0.08, "Refuse unsupported answer\nor escalate to an authorised channel", PALE_AMBER, AMBER)
    box(ax, 0.73, 0.24, 0.23, 0.08, "Regenerate once with stricter evidence;\notherwise refuse or escalate", PALE_AMBER, AMBER, fontsize=7.5)
    box(ax, 0.34, 0.01, 0.32, 0.07, "Record retrieval, checks, outcome and feedback", PALE_GRAY, "#666666")

    arrow(ax, (0.50, 0.91), (0.50, 0.855))
    arrow(ax, (0.50, 0.745), (0.50, 0.72))
    arrow(ax, (0.50, 0.65), (0.50, 0.595))
    arrow(ax, (0.50, 0.485), (0.50, 0.46))
    arrow(ax, (0.50, 0.39), (0.50, 0.335))
    arrow(ax, (0.50, 0.225), (0.50, 0.19))
    arrow(ax, (0.50, 0.12), (0.50, 0.08))

    arrow(ax, (0.33, 0.80), (0.27, 0.78), color=AMBER)
    ax.text(0.31, 0.825, "No", color=AMBER, fontsize=8, ha="right")
    ax.text(0.52, 0.735, "Yes", color=GREEN, fontsize=8)
    arrow(ax, (0.67, 0.54), (0.73, 0.54), color=AMBER)
    ax.text(0.69, 0.565, "No", color=AMBER, fontsize=8)
    ax.text(0.52, 0.475, "Yes", color=GREEN, fontsize=8)
    arrow(ax, (0.67, 0.28), (0.73, 0.28), color=AMBER)
    ax.text(0.69, 0.305, "No", color=AMBER, fontsize=8)
    ax.text(0.52, 0.215, "Yes", color=GREEN, fontsize=8)
    arrow(ax, (0.75, 0.32), (0.64, 0.425), color=AMBER, connectionstyle="arc3,rad=-0.15")
    ax.text(
        0.50,
        -0.012,
        "All clarification, refusal, escalation, retrieval and answer events are logged.",
        ha="center",
        va="top",
        fontsize=7.5,
        color="#666666",
    )

    fig.tight_layout(pad=0.2)
    for suffix in ("png", "svg"):
        fig.savefig(OUT / f"question_answer_flow.{suffix}", bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    architecture()
    answer_flow()
    print(OUT)
