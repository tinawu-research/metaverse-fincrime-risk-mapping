#!/usr/bin/env python3
"""Paper figure: K=11 topic -> threat associations (24 author-reviewed links).

Reads graph_pack/graph_data.json (written by 02_build_graph_k11_65docs.py) and draws only
the edges whose edge_origin is 'author_reviewed_k11_20261001'. Nothing is added or promoted.

Outputs figures/Figure_K11_topic_threat_associations.{png,pdf,svg}
Deterministic: fixed node order, fixed fonts, no timestamps in the files.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.dont_write_bytecode = True

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, PathPatch  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

matplotlib.rcParams["svg.hashsalt"] = "k11-65docs"
matplotlib.rcParams["svg.fonttype"] = "none"
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["font.family"] = "DejaVu Sans"

TOPIC_FILL = "#315c72"
THREAT_FILL = "#9b3d42"
EDGE = "#2b3a42"
UNMAPPED_FILL = "#e8ecee"

# Short threat names for the figure; the full definitions stay in graph_data.json.
THREAT_SHORT = {
    "TH_PAYMENT": "Digital payment, trust and\nfraud-detection environment",
    "TH_CYBER": "Cyberattack, malware, platform\nsecurity and infrastructure compromise",
    "TH_IDENTITY": "Avatar, identity, biometric and\naccount-takeover abuse",
    "TH_PRIVACY": "Privacy, data protection\nand traceability gaps",
    "TH_DEFI": "DeFi, smart-contract, DAO and\ngovernance-control misuse",
    "TH_SCAM": "Scams, fraud and social deception\n(incl. associated laundering)",
    "TH_GOVERNANCE": "Platform governance, jurisdiction\nand legal-accountability gaps",
    "TH_NFT": "NFT, gaming and virtual-property\nvalue manipulation",
    "TH_WALLET": "Wallet, exchange, off-ramp and\ncross-chain laundering exposure",
}
TOPIC_WRAP = {  # manual two-line wraps for the 11 agreed labels
    "T01": "Perceived trust, equality\nand consumer issues",
    "T02": "Data-driven attack detection\nand authentication",
    "T03": "Gameplay and review/\nresearch methods",
    "T04": "Technical trust, reputation\nand authenticity",
    "T05": "Governance of data\nand assets",
    "T06": "NFT ownership and\ndigital-asset markets",
    "T07": "Transaction and\nauthentication protocols",
    "T08": "Cryptoasset crime\nand scams",
    "T09": "NFT markets, value and\nfinancial perceptions",
    "T10": "Encryption, access control\nand network methods",
    "T11": "Broad metaverse-\nplatform security",
}
# Footnote markers on specific edges (explained in the caption).
EDGE_MARK = {("T04", "TH_CYBER"): "a", ("T08", "TH_DEFI"): "b"}


def barycentre_order(topics, threats, links):
    """Deterministic ordering of threats by mean position of their topics."""
    pos = {t: i for i, t in enumerate(topics)}
    inc = defaultdict(list)
    for s, t in links:
        inc[t].append(pos[s])
    key = {t: (sum(inc[t]) / len(inc[t]), t) for t in threats if inc[t]}
    return sorted(key, key=lambda t: key[t])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", required=True, help="graph_pack/graph_data.json")
    ap.add_argument("--out", required=True, help="figures output directory")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    g = json.loads(Path(args.graph).read_text(encoding="utf-8"))
    topics = [t["id"] for t in g["topics"]]
    prev = {t["id"]: t["prevalence"] for t in g["topics"]}
    links = [(e["source"], e["target"]) for e in g["edges"] if e.get("edge_origin") == "author_reviewed_k11_20261001"]
    qual = {(e["source"], e["target"]): e.get("qualifiers", "") for e in g["edges"] if e.get("edge_origin") == "author_reviewed_k11_20261001"}
    assert len(links) == 24 and len(set(links)) == 24
    threats = barycentre_order(topics, [t["id"] for t in g["threats"]], links)
    assert len(threats) == 9

    fig, ax = plt.subplots(figsize=(11.5, 9.2))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    top, bot = 91.0, 6.0
    ty = {t: top - i * (top - bot) / (len(topics) - 1) for i, t in enumerate(topics)}
    hy = {h: top - i * (top - bot) / (len(threats) - 1) for i, h in enumerate(threats)}
    xl, xr, wl, wr = 3.0, 62.0, 26.0, 35.0
    hl, hr = 6.4, 7.2

    mapped = {s for s, _ in links}
    for t in topics:
        face = TOPIC_FILL if t in mapped else UNMAPPED_FILL
        txtc = "white" if t in mapped else "#27343b"
        ax.add_patch(FancyBboxPatch((xl, ty[t] - hl / 2), wl, hl, boxstyle="round,pad=0.0,rounding_size=0.8",
                                    fc=face, ec="#172026", lw=0.8, zorder=3))
        ax.text(xl + 1.0, ty[t] + 0.1, f"{t}", color=txtc, fontsize=9.5, fontweight="bold", va="center", ha="left", zorder=4)
        ax.text(xl + 5.2, ty[t] + 0.1, TOPIC_WRAP[t], color=txtc, fontsize=8.2, va="center", ha="left", zorder=4, linespacing=1.05)
        ax.text(xl + wl - 0.8, ty[t] + 0.1, f"{prev[t]:.2f}%", color=txtc, fontsize=8.4, fontweight="bold", va="center", ha="right", zorder=4)
    for h in threats:
        ax.add_patch(FancyBboxPatch((xr, hy[h] - hr / 2), wr, hr, boxstyle="round,pad=0.0,rounding_size=0.8",
                                    fc=THREAT_FILL, ec="#172026", lw=0.8, zorder=3))
        ax.text(xr + 1.0, hy[h] + 1.7, h, color="white", fontsize=8.6, fontweight="bold", va="center", ha="left", zorder=4)
        ax.text(xr + 1.0, hy[h] - 0.9, THREAT_SHORT[h], color="white", fontsize=7.4, va="center", ha="left", zorder=4, linespacing=1.05)

    # T03 annotation (no approved link)
    ax.text(xl + wl + 1.5, ty["T03"], "no approved link", fontsize=7.8, style="italic", color="#4f5d66", va="center", ha="left", zorder=4)

    # edges: spread attachment points on each box so lines do not pile up
    out_n = defaultdict(int)
    in_n = defaultdict(int)
    for s, t in links:
        out_n[s] += 1
        in_n[t] += 1
    out_i = defaultdict(int)
    in_i = defaultdict(int)
    order = sorted(links, key=lambda e: (topics.index(e[0]), threats.index(e[1])))
    for s, t in order:
        k = out_i[s]
        out_i[s] += 1
        m = in_i[t]
        in_i[t] += 1
        y1 = ty[s] + (k - (out_n[s] - 1) / 2) * 1.0
        y2 = hy[t] + (m - (in_n[t] - 1) / 2) * 1.05
        x1, x2 = xl + wl, xr
        cx = (x1 + x2) / 2
        verts = [(x1, y1), (cx, y1), (cx, y2), (x2, y2)]
        codes = [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4]
        q = qual[(s, t)]
        if "perception_evidence" in q:
            ls = (0, (5, 2.5))
        elif "potential_future_quantum_risk_only" in q:
            ls = (0, (1.2, 2.2))
        else:
            ls = "-"
        ax.add_patch(PathPatch(MPath(verts, codes), fc="none", ec=EDGE, lw=1.35, ls=ls, alpha=0.72, zorder=2))
        if (s, t) in EDGE_MARK:
            # marker at the Bezier midpoint (t=0.5)
            mx = 0.125 * x1 + 0.375 * cx + 0.375 * cx + 0.125 * x2
            my = 0.125 * y1 + 0.375 * y1 + 0.375 * y2 + 0.125 * y2
            ax.text(mx, my, EDGE_MARK[(s, t)], fontsize=8, fontweight="bold", ha="center", va="center", zorder=5,
                    bbox=dict(boxstyle="circle,pad=0.18", fc="white", ec=EDGE, lw=0.8))

    ax.text(xl, 97.3, "K=11 topic (mean publication-level proportion, n = 65)", fontsize=9.5, fontweight="bold", color="#27343b", ha="left")
    ax.text(xr, 97.3, "Threat category", fontsize=9.5, fontweight="bold", color="#27343b", ha="left")

    handles = [
        Line2D([0], [0], color=EDGE, lw=1.6, label="Author-reviewed association"),
        Line2D([0], [0], color=EDGE, lw=1.6, ls=(0, (5, 2.5)), label="Perception-based evidence (T01, T06)"),
        Line2D([0], [0], color=EDGE, lw=1.6, ls=(0, (1.2, 2.2)), label="Potential future risk (T10 → TH_CYBER)"),
    ]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.0, -0.075), ncol=3, frameon=False, fontsize=8.2,
              handlelength=3.2, columnspacing=1.6)

    fig.tight_layout(pad=0.6)
    stem = out / "Figure_K11_topic_threat_associations"
    fig.savefig(str(stem) + ".png", dpi=300, metadata={"Software": "matplotlib"})
    fig.savefig(str(stem) + ".pdf", metadata={"Creator": "matplotlib", "CreationDate": None, "ModDate": None})
    fig.savefig(str(stem) + ".svg", metadata={"Date": None, "Creator": "matplotlib"})
    print("wrote", stem)


if __name__ == "__main__":
    main()
