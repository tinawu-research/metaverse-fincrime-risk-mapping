from __future__ import annotations

import csv
import html
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape


BASE_DIR = Path(
    r"C:\Users\mtiwar05\OneDrive - Charles Sturt University\CSU\Metaverse and Cryptocurrencies\Analysis\Codex\Results\Round 5\mirofish_local_qwen_free_analysis_20260527-112059"
)
EVIDENCE_CSV = BASE_DIR / "document_evidence_table.csv"
PACK_DIR = BASE_DIR / "free_full_graph_pack"


TOPICS = [
    {
        "id": "T6",
        "label": "Crypto finance, DeFi, scams, and grey-economy risks",
        "prevalence": 19.17,
        "documents": 13,
        "threats": ["TH_SCAM", "TH_WALLET", "TH_DEFI"],
    },
    {
        "id": "T2",
        "label": "Avatar privacy, cyberattack detection, and metaverse security",
        "prevalence": 18.53,
        "documents": 10,
        "threats": ["TH_IDENTITY", "TH_CYBER", "TH_PRIVACY"],
    },
    {
        "id": "T1",
        "label": "Blockchain-based metaverse governance, ownership, and token infrastructure",
        "prevalence": 16.30,
        "documents": 8,
        "threats": ["TH_GOVERNANCE", "TH_DEFI", "TH_NFT"],
    },
    {
        "id": "T7",
        "label": "Cryptographic access control, authentication, and encryption protocols",
        "prevalence": 13.64,
        "documents": 9,
        "threats": ["TH_IDENTITY", "TH_PRIVACY", "TH_CYBER"],
    },
    {
        "id": "T5",
        "label": "Blockchain gaming, NFT markets, and digital-property law",
        "prevalence": 13.37,
        "documents": 7,
        "threats": ["TH_NFT", "TH_SCAM", "TH_GOVERNANCE"],
    },
    {
        "id": "T3",
        "label": "Cryptocurrency networks, wallets, exchanges, and regulatory risk",
        "prevalence": 9.65,
        "documents": 7,
        "threats": ["TH_WALLET", "TH_DEFI", "TH_PAYMENT"],
    },
    {
        "id": "T4",
        "label": "Digital payments, privacy policy, trust, and fraud detection",
        "prevalence": 9.34,
        "documents": 5,
        "threats": ["TH_PAYMENT", "TH_PRIVACY", "TH_SCAM"],
    },
]


THREATS = [
    {
        "id": "TH_SCAM",
        "label": "Scam, fraud, and social-deception laundering opportunities",
        "keywords": [
            "fraud",
            "scam",
            "social engineering",
            "phishing",
            "cybercrime",
            "financial fraud",
            "money laundering",
            "laundering",
        ],
        "layer": "LY_OPPORTUNITY",
        "signal": "SG_SCAM",
        "interventions": ["IN_SCAM_MONITOR", "IN_EVIDENCE", "IN_MARKETPLACE"],
    },
    {
        "id": "TH_IDENTITY",
        "label": "Avatar, identity, biometric, and account takeover abuse",
        "keywords": [
            "avatar",
            "identity",
            "biometric",
            "deepfake",
            "authentication",
            "account",
            "fingerprint",
            "credential",
        ],
        "layer": "LY_IDENTITY",
        "signal": "SG_AVATAR",
        "interventions": ["IN_ONBOARDING", "IN_ACCESS", "IN_EVIDENCE"],
    },
    {
        "id": "TH_NFT",
        "label": "NFT, gaming, and virtual-property value manipulation",
        "keywords": [
            "nft",
            "non-fungible",
            "gaming",
            "game",
            "digital asset",
            "virtual asset",
            "property",
            "marketplace",
            "wash",
        ],
        "layer": "LY_ASSET",
        "signal": "SG_NFT",
        "interventions": ["IN_PROVENANCE", "IN_MARKETPLACE", "IN_VALUATION"],
    },
    {
        "id": "TH_WALLET",
        "label": "Wallet, exchange, off-ramp, and cross-chain laundering exposure",
        "keywords": [
            "wallet",
            "exchange",
            "bitcoin",
            "cryptocurrency",
            "crypto",
            "transaction",
            "off-ramp",
            "mixer",
            "bridge",
            "address",
        ],
        "layer": "LY_TRANSACTION",
        "signal": "SG_WALLET",
        "interventions": ["IN_CHAIN_ANALYTICS", "IN_OFFRAMP", "IN_EVIDENCE"],
    },
    {
        "id": "TH_DEFI",
        "label": "DeFi, smart-contract, DAO, and governance-control misuse",
        "keywords": [
            "defi",
            "decentralized",
            "smart contract",
            "dao",
            "protocol",
            "governance",
            "token",
            "treasury",
        ],
        "layer": "LY_GOVERNANCE",
        "signal": "SG_CONTRACT",
        "interventions": ["IN_GOVERNANCE_AUDIT", "IN_CHAIN_ANALYTICS", "IN_PROVENANCE"],
    },
    {
        "id": "TH_PRIVACY",
        "label": "Privacy, data protection, and traceability gaps",
        "keywords": [
            "privacy",
            "data protection",
            "personal data",
            "confidential",
            "encryption",
            "anonymous",
            "anonymity",
            "traceability",
        ],
        "layer": "LY_IDENTITY",
        "signal": "SG_PRIVACY",
        "interventions": ["IN_ACCESS", "IN_PRIVACY_BY_DESIGN", "IN_EVIDENCE"],
    },
    {
        "id": "TH_PAYMENT",
        "label": "Digital payment, trust, fraud-detection, and Sybil-risk environment",
        "keywords": [
            "payment",
            "trust",
            "fraud detection",
            "sybil",
            "transaction pattern",
            "anomaly",
            "risk detection",
        ],
        "layer": "LY_TRANSACTION",
        "signal": "SG_PAYMENT",
        "interventions": ["IN_PAYMENT_CONTROLS", "IN_CHAIN_ANALYTICS", "IN_OFFRAMP"],
    },
    {
        "id": "TH_CYBER",
        "label": "Cyberattack, malware, platform-security, and infrastructure compromise",
        "keywords": [
            "cyberattack",
            "malware",
            "cybersecurity",
            "attack",
            "security",
            "vulnerability",
            "malicious",
            "threat",
        ],
        "layer": "LY_PLATFORM",
        "signal": "SG_CYBER",
        "interventions": ["IN_PLATFORM_SECURITY", "IN_ACCESS", "IN_EVIDENCE"],
    },
    {
        "id": "TH_GOVERNANCE",
        "label": "Platform governance, jurisdictional, and legal accountability gaps",
        "keywords": [
            "law",
            "regulation",
            "regulatory",
            "jurisdiction",
            "governance",
            "compliance",
            "legal",
            "accountability",
        ],
        "layer": "LY_GOVERNANCE",
        "signal": "SG_GOVERNANCE",
        "interventions": ["IN_GOVERNANCE_AUDIT", "IN_OFFRAMP", "IN_EVIDENCE"],
    },
]


LAYERS = [
    ("LY_PLATFORM", "Platform affordances: avatars, immersion, persistence, social presence"),
    ("LY_IDENTITY", "Identity-access layer: accounts, avatars, biometrics, credentials"),
    ("LY_ASSET", "Asset-market layer: NFTs, tokens, game items, virtual property"),
    ("LY_TRANSACTION", "Transaction-flow layer: wallets, payments, bridges, exchanges"),
    ("LY_GOVERNANCE", "Governance-control layer: DAOs, contracts, rules, jurisdiction"),
    ("LY_OPPORTUNITY", "Opportunity-formation layer: anonymity, deception, fragmented controls"),
    ("LY_DETECTION", "Detection-intervention layer: evidence, analytics, policy controls"),
]


SIGNALS = [
    ("SG_SCAM", "Scam campaign and social-engineering signals"),
    ("SG_AVATAR", "Avatar/account anomaly signals"),
    ("SG_NFT", "NFT wash-trade, provenance, and value-anomaly signals"),
    ("SG_WALLET", "Wallet clustering, mixer, bridge, and off-ramp exposure signals"),
    ("SG_CONTRACT", "Smart-contract, DAO, treasury, and permission-risk signals"),
    ("SG_PRIVACY", "Privacy, encryption, and traceability-loss signals"),
    ("SG_PAYMENT", "Payment, fraud-detection, trust, and Sybil signals"),
    ("SG_CYBER", "Cyberattack, malware, and platform compromise signals"),
    ("SG_GOVERNANCE", "Legal, compliance, and cross-jurisdiction signals"),
]


INTERVENTIONS = [
    ("IN_SCAM_MONITOR", "Scam-campaign monitoring and user harm response"),
    ("IN_ONBOARDING", "Risk-based onboarding and identity assurance"),
    ("IN_ACCESS", "Authentication, key custody, and access-control monitoring"),
    ("IN_PLATFORM_SECURITY", "Platform security monitoring and vulnerability response"),
    ("IN_PROVENANCE", "NFT/token provenance and asset-origin review"),
    ("IN_MARKETPLACE", "Marketplace behaviour monitoring and scam suppression"),
    ("IN_VALUATION", "Virtual-asset valuation and wash-trade anomaly review"),
    ("IN_CHAIN_ANALYTICS", "Wallet, bridge, mixer, and cross-chain analytics"),
    ("IN_PAYMENT_CONTROLS", "Digital-payment fraud controls and trust scoring"),
    ("IN_GOVERNANCE_AUDIT", "Smart-contract, DAO, and governance audit controls"),
    ("IN_OFFRAMP", "Exchange/off-ramp due diligence and reporting"),
    ("IN_EVIDENCE", "Investigation, evidence preservation, and case escalation"),
    ("IN_PRIVACY_BY_DESIGN", "Privacy-by-design controls with auditability"),
]


DIMENSIONS = [
    ("metaverse_platform_features", "Metaverse platform features"),
    ("crypto_ecosystem_features", "Cryptocurrency ecosystem features"),
    ("financial_crime_opportunities", "Financial crime opportunities"),
    ("modelling_analysis_intervention", "Modelling, analysis, and intervention"),
]


TYPE_COLOR = {
    "topic": "#315c72",
    "threat": "#9b3d42",
    "layer": "#6f5b2f",
    "signal": "#526d3f",
    "intervention": "#2f6f62",
    "document": "#6a5a9a",
    "dimension": "#4f6f98",
}


def clean_title(filename: str) -> str:
    text = re.sub(r"\.(pdf|txt)$", "", filename, flags=re.I)
    text = text.replace("_compressed", "").replace("_extract", "")
    text = text.replace("_", " ")
    return re.sub(r"\s+", " ", text).strip()


def short_label(text: str, max_len: int = 72) -> str:
    text = re.sub(r"\s+", " ", str(text)).strip()
    if len(text) <= max_len:
        return text
    cut = text[: max_len - 1].rsplit(" ", 1)[0]
    return cut + "..."


def wrap_text(text: str, width: int) -> list[str]:
    words = re.sub(r"\s+", " ", str(text)).strip().split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else current + " " + word
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def to_int(value: str) -> int:
    try:
        return int(float(value))
    except Exception:
        return 0


def node(
    node_id: str,
    label: str,
    node_type: str,
    detail: str = "",
    **attrs,
) -> dict:
    base = {
        "id": node_id,
        "label": label,
        "type": node_type,
        "detail": detail,
    }
    base.update(attrs)
    return base


def edge(
    source: str,
    target: str,
    relation: str,
    weight: float = 1.0,
    evidence: str = "",
    **attrs,
) -> dict:
    base = {
        "source": source,
        "target": target,
        "relation": relation,
        "weight": round(float(weight), 4),
        "evidence": evidence,
    }
    base.update(attrs)
    return base


def load_documents() -> list[dict]:
    with EVIDENCE_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    docs = []
    for row in rows:
        dim_counts = {key: to_int(row.get(key, "0")) for key, _ in DIMENSIONS}
        total_score = sum(dim_counts.values())
        text_blob = " ".join(
            [
                row.get("filename", ""),
                row.get("relevance", ""),
                row.get("top_evidence_1", ""),
                row.get("top_evidence_2", ""),
                row.get("top_evidence_3", ""),
            ]
        ).lower()
        threat_scores = {}
        for threat in THREATS:
            count = 0
            for keyword in threat["keywords"]:
                count += len(re.findall(re.escape(keyword.lower()), text_blob))
            if count:
                threat_scores[threat["id"]] = count

        if not threat_scores:
            # Keep every document in the graph even when keyword detection is sparse.
            best_dim = max(dim_counts, key=dim_counts.get)
            fallback = {
                "metaverse_platform_features": "TH_CYBER",
                "crypto_ecosystem_features": "TH_WALLET",
                "financial_crime_opportunities": "TH_SCAM",
                "modelling_analysis_intervention": "TH_PAYMENT",
            }[best_dim]
            threat_scores[fallback] = 1

        top_threats = sorted(threat_scores.items(), key=lambda x: (-x[1], x[0]))[:3]
        doc_no = row["doc_id"].split("_", 1)[0]
        title = clean_title(row.get("filename", row["doc_id"]))
        docs.append(
            {
                "id": "DOC_" + doc_no,
                "doc_no": doc_no,
                "source_doc_id": row["doc_id"],
                "title": title,
                "filename": row.get("filename", ""),
                "pages": to_int(row.get("pages", "0")),
                "words": to_int(row.get("extracted_words", "0")),
                "relevance": row.get("relevance", ""),
                "dim_counts": dim_counts,
                "total_score": total_score,
                "top_threats": top_threats,
                "evidence": [
                    row.get("top_evidence_1", ""),
                    row.get("top_evidence_2", ""),
                    row.get("top_evidence_3", ""),
                ],
            }
        )
    return docs


def build_graph(docs: list[dict]) -> tuple[list[dict], list[dict]]:
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    for topic in TOPICS:
        nodes[topic["id"]] = node(
            topic["id"],
            topic["id"] + ": " + topic["label"],
            "topic",
            f"{topic['prevalence']}% topic prevalence; dominant in {topic['documents']} PDFs.",
            prevalence=topic["prevalence"],
            documents=topic["documents"],
        )
        for threat_id in topic["threats"]:
            edges.append(
                edge(
                    topic["id"],
                    threat_id,
                    "topic-identifies-emerging-threat",
                    topic["prevalence"],
                )
            )

    for threat in THREATS:
        nodes[threat["id"]] = node(threat["id"], threat["label"], "threat")
        edges.append(edge(threat["id"], threat["layer"], "threat-operates-through-layer", 2))
        edges.append(edge(threat["id"], threat["signal"], "modelled-by-signal", 2))
        for intervention_id in threat["interventions"]:
            edges.append(edge(threat["id"], intervention_id, "intervention-point", 2))

    for layer_id, label in LAYERS:
        nodes[layer_id] = node(layer_id, label, "layer")
        edges.append(edge(layer_id, "LY_DETECTION", "feeds-detection-and-intervention", 1.2))

    for signal_id, label in SIGNALS:
        nodes[signal_id] = node(signal_id, label, "signal")
        edges.append(edge(signal_id, "LY_DETECTION", "analytical-signal", 1.2))

    for intervention_id, label in INTERVENTIONS:
        nodes[intervention_id] = node(intervention_id, label, "intervention")
        edges.append(edge("LY_DETECTION", intervention_id, "converted-into-control", 1))

    for dim_id, dim_label in DIMENSIONS:
        nodes["DIM_" + dim_id] = node(
            "DIM_" + dim_id,
            dim_label,
            "dimension",
            "Evidence dimension counted from the extracted PDF text.",
        )

    max_score = max((doc["total_score"] for doc in docs), default=1)
    max_dim = max((max(doc["dim_counts"].values()) for doc in docs), default=1)
    for doc in docs:
        doc_id = doc["id"]
        evidence_preview = " | ".join(short_label(x, 180) for x in doc["evidence"] if x)
        nodes[doc_id] = node(
            doc_id,
            f"{doc['doc_no']}: {short_label(doc['title'], 62)}",
            "document",
            evidence_preview,
            source_doc_id=doc["source_doc_id"],
            title=doc["title"],
            filename=doc["filename"],
            relevance=doc["relevance"],
            pages=doc["pages"],
            words=doc["words"],
            total_score=doc["total_score"],
            evidence=doc["evidence"],
        )
        for dim_id, dim_label in DIMENSIONS:
            count = doc["dim_counts"].get(dim_id, 0)
            if count > 0:
                edges.append(
                    edge(
                        doc_id,
                        "DIM_" + dim_id,
                        "document-supports-evidence-dimension",
                        1 + (count / max_dim) * 8,
                        f"{count} keyword/evidence hits for {dim_label}",
                        count=count,
                    )
                )
        for threat_id, count in doc["top_threats"]:
            edges.append(
                edge(
                    doc_id,
                    threat_id,
                    "document-indicates-threat",
                    1 + count,
                    f"{count} keyword matches in title/evidence excerpts",
                    count=count,
                )
            )
        if doc["total_score"] >= max_score * 0.55:
            # Make the strongest documents visible in the semantic layer as empirical anchors.
            strongest_threat = doc["top_threats"][0][0]
            edges.append(
                edge(
                    doc_id,
                    strongest_threat,
                    "high-evidence-anchor",
                    4,
                    f"High evidence score: {doc['total_score']}",
                )
            )

    return list(nodes.values()), edges


def write_csvs(nodes: list[dict], edges: list[dict]) -> None:
    node_keys = [
        "id",
        "label",
        "type",
        "detail",
        "prevalence",
        "documents",
        "source_doc_id",
        "filename",
        "relevance",
        "pages",
        "words",
        "total_score",
    ]
    with (PACK_DIR / "graph_nodes.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=node_keys, extrasaction="ignore")
        writer.writeheader()
        for n in nodes:
            writer.writerow(n)

    edge_keys = ["source", "target", "relation", "weight", "evidence", "count"]
    with (PACK_DIR / "graph_edges.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=edge_keys, extrasaction="ignore")
        writer.writeheader()
        for e in edges:
            writer.writerow(e)


def write_graphml(nodes: list[dict], edges: list[dict]) -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '<key id="label" for="node" attr.name="label" attr.type="string"/>',
        '<key id="type" for="node" attr.name="type" attr.type="string"/>',
        '<key id="detail" for="node" attr.name="detail" attr.type="string"/>',
        '<key id="relation" for="edge" attr.name="relation" attr.type="string"/>',
        '<key id="weight" for="edge" attr.name="weight" attr.type="double"/>',
        '<key id="evidence" for="edge" attr.name="evidence" attr.type="string"/>',
        '<graph id="MetaverseCryptoFinancialCrime" edgedefault="directed">',
    ]
    for n in nodes:
        lines.append(f'  <node id="{xml_escape(n["id"])}">')
        lines.append(f'    <data key="label">{xml_escape(str(n.get("label", "")))}</data>')
        lines.append(f'    <data key="type">{xml_escape(str(n.get("type", "")))}</data>')
        lines.append(f'    <data key="detail">{xml_escape(str(n.get("detail", "")))}</data>')
        lines.append("  </node>")
    for i, e in enumerate(edges, 1):
        lines.append(
            f'  <edge id="e{i}" source="{xml_escape(e["source"])}" target="{xml_escape(e["target"])}">'
        )
        lines.append(f'    <data key="relation">{xml_escape(str(e.get("relation", "")))}</data>')
        lines.append(f'    <data key="weight">{e.get("weight", 1)}</data>')
        lines.append(f'    <data key="evidence">{xml_escape(str(e.get("evidence", "")))}</data>')
        lines.append("  </edge>")
    lines.append("  </graph>")
    lines.append("</graphml>")
    (PACK_DIR / "graph_data.graphml").write_text("\n".join(lines), encoding="utf-8")


def svg_text(
    x: float,
    y: float,
    text: str,
    width: int,
    size: int = 12,
    anchor: str = "middle",
    fill: str = "#172026",
    weight: str = "500",
) -> str:
    lines = wrap_text(text, width)
    out = []
    start_y = y - (len(lines) - 1) * (size * 0.62)
    for i, line in enumerate(lines):
        out.append(
            f'<text x="{x:.1f}" y="{start_y + i * size * 1.2:.1f}" text-anchor="{anchor}" '
            f'font-size="{size}" font-weight="{weight}" fill="{fill}">{html.escape(line)}</text>'
        )
    return "\n".join(out)


def node_svg(
    n: dict,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str | None = None,
    node_type: str | None = None,
    extra_class: str = "",
) -> str:
    node_type = node_type or n.get("type", "")
    color = TYPE_COLOR.get(node_type, "#58606b")
    label = label if label is not None else n.get("label", n.get("id", ""))
    detail = n.get("detail", "")
    cls = f"node {node_type} {extra_class}".strip()
    return f"""
<g class="{cls}" data-type="{html.escape(node_type)}" data-node-id="{html.escape(n.get('id',''))}">
  <title>{html.escape(n.get('label',''))}&#10;{html.escape(detail)}</title>
  <rect x="{x - w/2:.1f}" y="{y - h/2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="7" fill="{color}" stroke="#172026" stroke-opacity="0.18" stroke-width="1.2"/>
  {svg_text(x, y - min(12, h * 0.13), label, max(12, int(w / 7.1)), 12 if w > 95 else 10, fill="#ffffff", weight="650")}
</g>
"""


def edge_svg(x1: float, y1: float, x2: float, y2: float, weight: float, relation: str = "") -> str:
    width = 0.6 + min(4.0, math.sqrt(max(weight, 0.1)) * 0.55)
    opacity = 0.18 + min(0.34, math.sqrt(max(weight, 0.1)) * 0.035)
    mid = (x1 + x2) / 2
    d = f"M {x1:.1f},{y1:.1f} C {mid:.1f},{y1:.1f} {mid:.1f},{y2:.1f} {x2:.1f},{y2:.1f}"
    return (
        f'<path class="edge" d="{d}" fill="none" stroke="#53616b" '
        f'stroke-width="{width:.2f}" stroke-opacity="{opacity:.2f}"><title>{html.escape(relation)}</title></path>'
    )


def semantic_layout(nodes: list[dict]) -> dict[str, tuple[float, float, float, float]]:
    by_type = defaultdict(list)
    for n in nodes:
        if n["type"] != "document" and n["type"] != "dimension":
            by_type[n["type"]].append(n)

    for t in by_type:
        by_type[t].sort(key=lambda n: n["id"])

    layout = {}

    def place(items, x, top, bottom, w, h):
        step = (bottom - top) / max(1, len(items) - 1)
        for i, n in enumerate(items):
            y = (top + bottom) / 2 if len(items) == 1 else top + i * step
            layout[n["id"]] = (x, y, w, h)

    topic_order = [next(n for n in nodes if n["id"] == t["id"]) for t in TOPICS]
    threat_order = [next(n for n in nodes if n["id"] == t["id"]) for t in THREATS]
    layer_order = [next(n for n in nodes if n["id"] == t[0]) for t in LAYERS]
    signal_order = [next(n for n in nodes if n["id"] == t[0]) for t in SIGNALS]
    intervention_order = [next(n for n in nodes if n["id"] == t[0]) for t in INTERVENTIONS]

    place(topic_order, 130, 100, 820, 190, 74)
    place(threat_order, 390, 80, 840, 210, 68)
    place(layer_order, 660, 95, 480, 210, 62)
    place(signal_order, 660, 570, 855, 210, 54)
    place(intervention_order, 930, 75, 855, 220, 54)
    return layout


def make_semantic_svg(nodes: list[dict], edges: list[dict]) -> str:
    layout = semantic_layout(nodes)
    edge_bits = []
    for e in edges:
        if e["source"] in layout and e["target"] in layout:
            x1, y1, w1, _ = layout[e["source"]]
            x2, y2, w2, _ = layout[e["target"]]
            edge_bits.append(edge_svg(x1 + w1 / 2, y1, x2 - w2 / 2, y2, e["weight"], e["relation"]))

    node_map = {n["id"]: n for n in nodes}
    node_bits = []
    for node_id, (x, y, w, h) in layout.items():
        n = node_map[node_id]
        label = n["label"]
        if n["type"] == "topic":
            label = label.replace(": ", "\n")
        node_bits.append(node_svg(n, x, y, w, h, label=label))

    legend = []
    legend_items = [
        ("topic", "Topic model output"),
        ("threat", "Emerging financial-crime environment"),
        ("layer", "Modelling layer"),
        ("signal", "Analytical signal"),
        ("intervention", "Intervention point"),
    ]
    for i, (typ, lab) in enumerate(legend_items):
        x = 105 + i * 210
        legend.append(
            f'<rect x="{x}" y="924" width="15" height="15" rx="3" fill="{TYPE_COLOR[typ]}"/>'
            f'<text x="{x+22}" y="936" font-size="12" fill="#26323a">{html.escape(lab)}</text>'
        )

    return f"""<svg class="graph-svg semantic-svg" xmlns="http://www.w3.org/2000/svg" width="1120" height="960" viewBox="0 0 1120 960" role="img" aria-label="Topic threat intervention network">
<style>
  .graph-title {{ font: 700 22px Arial, sans-serif; fill: #172026; }}
  .graph-subtitle {{ font: 400 13px Arial, sans-serif; fill: #4f5d66; }}
  text {{ font-family: Arial, sans-serif; }}
  .node {{ cursor: default; }}
  .edge {{ pointer-events: stroke; }}
</style>
<rect width="1120" height="960" fill="#f7f8f5"/>
<text x="54" y="42" class="graph-title">Full Topic-to-Threat-to-Intervention Graph</text>
<text x="54" y="66" class="graph-subtitle">Built locally from Round 5 topic modelling, Qwen evidence extraction, and the 59-document corpus.</text>
<text x="130" y="92" text-anchor="middle" font-size="12" font-weight="700" fill="#46545d">Topic model</text>
<text x="390" y="58" text-anchor="middle" font-size="12" font-weight="700" fill="#46545d">Emerging threat environment</text>
<text x="660" y="58" text-anchor="middle" font-size="12" font-weight="700" fill="#46545d">Model and analyse</text>
<text x="930" y="58" text-anchor="middle" font-size="12" font-weight="700" fill="#46545d">Intervention points</text>
{"".join(edge_bits)}
{"".join(node_bits)}
{"".join(legend)}
</svg>"""


def make_document_svg(nodes: list[dict], edges: list[dict], docs: list[dict]) -> str:
    node_map = {n["id"]: n for n in nodes}
    doc_nodes = [node_map[d["id"]] for d in docs]
    dim_nodes = [node_map["DIM_" + dim_id] for dim_id, _ in DIMENSIONS]
    threat_nodes = [node_map[t["id"]] for t in THREATS]

    layout: dict[str, tuple[float, float, float, float]] = {}
    cx, cy = 650.0, 620.0
    doc_radius = 480.0
    threat_radius = 275.0
    dim_radius = 135.0

    for i, n in enumerate(doc_nodes):
        angle = -math.pi / 2 + i * (2 * math.pi / len(doc_nodes))
        layout[n["id"]] = (cx + math.cos(angle) * doc_radius, cy + math.sin(angle) * doc_radius, 54, 30)

    for i, n in enumerate(threat_nodes):
        angle = -math.pi / 2 + i * (2 * math.pi / len(threat_nodes))
        layout[n["id"]] = (cx + math.cos(angle) * threat_radius, cy + math.sin(angle) * threat_radius, 122, 48)

    for i, n in enumerate(dim_nodes):
        angle = -math.pi / 2 + i * (2 * math.pi / len(dim_nodes))
        layout[n["id"]] = (cx + math.cos(angle) * dim_radius, cy + math.sin(angle) * dim_radius, 148, 52)

    edge_bits = []
    for e in edges:
        if e["source"] in layout and e["target"] in layout:
            # Keep the full graph, but cap visual line width to keep it readable.
            x1, y1, w1, _ = layout[e["source"]]
            x2, y2, w2, _ = layout[e["target"]]
            edge_bits.append(edge_svg(x1, y1, x2, y2, min(e["weight"], 7), e["relation"]))

    node_bits = []
    for n in dim_nodes + threat_nodes:
        x, y, w, h = layout[n["id"]]
        node_bits.append(node_svg(n, x, y, w, h, label=short_label(n["label"], 42)))

    for n in doc_nodes:
        x, y, w, h = layout[n["id"]]
        score = int(n.get("total_score", 0))
        color = "#6a5a9a" if "primary" in n.get("relevance", "") else "#8a7bb3"
        node_bits.append(
            f"""
<g class="node document" data-type="document" data-node-id="{html.escape(n['id'])}">
  <title>{html.escape(n.get('label',''))}&#10;Evidence score: {score}&#10;{html.escape(n.get('detail',''))}</title>
  <circle cx="{x:.1f}" cy="{y:.1f}" r="{11 + min(7, math.sqrt(max(score, 1)) / 5):.1f}" fill="{color}" stroke="#172026" stroke-opacity="0.18"/>
  <text x="{x:.1f}" y="{y+4:.1f}" text-anchor="middle" font-size="9" font-weight="700" fill="#ffffff">{html.escape(n['id'].replace('DOC_', ''))}</text>
</g>
"""
        )

    legend = """
<rect x="72" y="1095" width="16" height="16" rx="3" fill="#4f6f98"/><text x="96" y="1108" font-size="12" fill="#26323a">Evidence dimension</text>
<rect x="250" y="1095" width="16" height="16" rx="3" fill="#9b3d42"/><text x="274" y="1108" font-size="12" fill="#26323a">Threat environment</text>
<circle cx="458" cy="1103" r="9" fill="#6a5a9a"/><text x="475" y="1108" font-size="12" fill="#26323a">Document node, scaled by evidence score</text>
"""
    return f"""<svg class="graph-svg document-svg" xmlns="http://www.w3.org/2000/svg" width="1300" height="1140" viewBox="0 0 1300 1140" role="img" aria-label="Document evidence network">
<style>
  .graph-title {{ font: 700 22px Arial, sans-serif; fill: #172026; }}
  .graph-subtitle {{ font: 400 13px Arial, sans-serif; fill: #4f5d66; }}
  text {{ font-family: Arial, sans-serif; }}
  .node {{ cursor: default; }}
</style>
<rect width="1300" height="1140" fill="#f7f8f5"/>
<text x="56" y="42" class="graph-title">Full Document Evidence Network</text>
<text x="56" y="66" class="graph-subtitle">All 59 PDFs are included. Edges connect documents to evidence dimensions and detected threat environments.</text>
{"".join(edge_bits)}
{"".join(node_bits)}
{legend}
</svg>"""


def make_lifecycle_svg() -> str:
    stages = [
        ("1", "Platform affordance", "Avatars, immersive spaces, user accounts, social interaction, persistent commerce"),
        ("2", "Crypto rail", "Wallets, tokens, NFTs, smart contracts, bridges, exchanges, digital payments"),
        ("3", "Opportunity formation", "Pseudonymity, rapid value transfer, fragmented jurisdiction, social deception"),
        ("4", "Financial-crime pattern", "Laundering, scams, fraud, theft, wash trading, mule/off-ramp use"),
        ("5", "Analytical model", "Topic-model themes, document evidence, graph links, transaction and behaviour signals"),
        ("6", "Intervention point", "Onboarding, marketplace, access control, chain analytics, off-ramp due diligence, evidence preservation"),
    ]
    interventions = [
        (122, 300, "Design-time controls", "Privacy with auditability; security-by-design; asset rules"),
        (322, 300, "Entry controls", "Risk-based onboarding; wallet and account assurance"),
        (522, 300, "Market controls", "NFT provenance; wash-trade review; scam suppression"),
        (722, 300, "Flow controls", "Wallet clustering; bridge/mixer exposure; payment anomaly detection"),
        (922, 300, "Exit controls", "Exchange/off-ramp due diligence; suspicious activity escalation"),
        (1122, 300, "Case controls", "Evidence preservation; cross-platform investigation; reporting"),
    ]
    bits = [
        '<svg class="graph-svg lifecycle-svg" xmlns="http://www.w3.org/2000/svg" width="1240" height="520" viewBox="0 0 1240 520" role="img" aria-label="Intervention lifecycle map">',
        "<style>text{font-family:Arial,sans-serif}.edge{stroke:#53616b;stroke-width:2;stroke-opacity:.44;fill:none}.arrow{fill:#53616b}.title{font:700 22px Arial,sans-serif;fill:#172026}.subtitle{font:400 13px Arial,sans-serif;fill:#4f5d66}</style>",
        '<rect width="1240" height="520" fill="#f7f8f5"/>',
        '<text x="48" y="42" class="title">Lifecycle Map: Where to Model, Analyse, and Intervene</text>',
        '<text x="48" y="66" class="subtitle">The graph converts topic-modelled emerging threats into practical intervention points across the metaverse-crypto crime environment.</text>',
    ]
    y = 150
    for i, (num, title, desc) in enumerate(stages):
        x = 82 + i * 205
        color = ["#315c72", "#4f6f98", "#9b3d42", "#8b4b2d", "#526d3f", "#2f6f62"][i]
        bits.append(
            f'<g class="node lifecycle-stage" data-type="layer"><rect x="{x-70}" y="{y-55}" width="155" height="110" rx="7" fill="{color}" stroke="#172026" stroke-opacity=".16"/>'
        )
        bits.append(f'<circle cx="{x-48}" cy="{y-33}" r="15" fill="#ffffff" fill-opacity=".92"/><text x="{x-48}" y="{y-28}" text-anchor="middle" font-size="13" font-weight="700" fill="{color}">{num}</text>')
        bits.append(svg_text(x + 10, y - 12, title, 17, 13, fill="#ffffff", weight="700"))
        bits.append(svg_text(x + 8, y + 30, desc, 22, 10, fill="#ffffff", weight="500"))
        bits.append("</g>")
        if i < len(stages) - 1:
            x2 = x + 125
            bits.append(f'<path class="edge" d="M{x+86},{y} L{x2},{y}"/><path class="arrow" d="M{x2},{y} l-8,-5 v10 z"/>')
    bits.append('<text x="48" y="262" font-size="13" font-weight="700" fill="#46545d">Intervention control surface</text>')
    for x, y2, title, desc in interventions:
        bits.append(
            f'<g class="node intervention" data-type="intervention"><rect x="{x-82}" y="{y2}" width="164" height="118" rx="7" fill="#2f6f62" stroke="#172026" stroke-opacity=".16"/>'
        )
        bits.append(svg_text(x, y2 + 34, title, 20, 13, fill="#ffffff", weight="700"))
        bits.append(svg_text(x, y2 + 76, desc, 25, 10, fill="#ffffff", weight="500"))
        bits.append("</g>")
        bits.append(f'<path d="M{x},{y2} C{x},{260} {x},{245} {x},{210}" fill="none" stroke="#2f6f62" stroke-width="1.4" stroke-opacity=".42" stroke-dasharray="5 5"/>')
    bits.append("</svg>")
    return "\n".join(bits)


def write_intervention_matrix(nodes: list[dict], edges: list[dict]) -> None:
    threat_lookup = {t["id"]: t["label"] for t in THREATS}
    int_lookup = dict(INTERVENTIONS)
    signal_lookup = dict(SIGNALS)
    layer_lookup = dict(LAYERS)
    threat_doc_counts = Counter()
    for e in edges:
        if e["relation"] in {"document-indicates-threat", "high-evidence-anchor"} and e["target"].startswith("TH_"):
            threat_doc_counts[e["target"]] += 1

    rows = []
    for t in THREATS:
        rows.append(
            {
                "threat_environment": threat_lookup[t["id"]],
                "modelling_layer": layer_lookup[t["layer"]],
                "analytical_signal": signal_lookup[t["signal"]],
                "intervention_points": "; ".join(int_lookup[i] for i in t["interventions"]),
                "linked_document_count": threat_doc_counts[t["id"]],
                "topic_links": "; ".join(topic["id"] for topic in TOPICS if t["id"] in topic["threats"]),
            }
        )
    with (PACK_DIR / "intervention_matrix.csv").open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "threat_environment",
            "modelling_layer",
            "analytical_signal",
            "intervention_points",
            "linked_document_count",
            "topic_links",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def make_html(nodes: list[dict], edges: list[dict], docs: list[dict], semantic_svg: str, document_svg: str, lifecycle_svg: str) -> str:
    type_counts = Counter(n["type"] for n in nodes)
    relation_counts = Counter(e["relation"] for e in edges)
    docs_sorted = sorted(docs, key=lambda d: (-d["total_score"], d["doc_no"]))
    top_doc_rows = []
    for d in docs_sorted:
        threats = ", ".join(t for t, _ in d["top_threats"])
        dims = ", ".join(f"{key.replace('_', ' ')}={value}" for key, value in d["dim_counts"].items())
        top_doc_rows.append(
            f"<tr data-search='{html.escape((d['doc_no'] + ' ' + d['title'] + ' ' + d['relevance']).lower())}'>"
            f"<td>{html.escape(d['doc_no'])}</td><td>{html.escape(short_label(d['title'], 95))}</td>"
            f"<td>{d['total_score']}</td><td>{html.escape(d['relevance'])}</td>"
            f"<td>{html.escape(threats)}</td><td>{html.escape(dims)}</td></tr>"
        )

    graph_data = {
        "created_by": "Codex local/free graph builder",
        "cost_boundary": "No paid API, no cloud graph service, no external web libraries.",
        "corpus": {"documents": len(docs), "source": str(EVIDENCE_CSV)},
        "nodes": nodes,
        "edges": edges,
    }
    graph_json = json.dumps(graph_data, ensure_ascii=False)
    safe_graph_json = graph_json.replace("<", "\\u003c").replace("</script", "<\\/script")
    stats_cards = [
        ("Documents", len(docs)),
        ("Graph nodes", len(nodes)),
        ("Graph edges", len(edges)),
        ("Topic model themes", len(TOPICS)),
        ("Threat environments", len(THREATS)),
        ("Intervention points", len(INTERVENTIONS)),
    ]
    stats_html = "".join(
        f"<div class='stat'><strong>{value}</strong><span>{html.escape(label)}</span></div>"
        for label, value in stats_cards
    )
    type_html = "".join(
        f"<label><input type='checkbox' data-type-toggle='{html.escape(typ)}' checked> {html.escape(typ)} ({count})</label>"
        for typ, count in sorted(type_counts.items())
    )
    relation_html = "".join(
        f"<li><strong>{html.escape(rel)}</strong>: {count}</li>" for rel, count in sorted(relation_counts.items())
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Free Full Graph Pack - Metaverse Crypto Financial Crime</title>
<style>
  :root {{
    --ink: #172026;
    --muted: #58656f;
    --line: #d8ddd8;
    --paper: #f7f8f5;
    --panel: #ffffff;
    --accent: #315c72;
    --teal: #2f6f62;
    --red: #9b3d42;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: Arial, Helvetica, sans-serif;
    color: var(--ink);
    background: var(--paper);
  }}
  header {{
    padding: 28px 34px 18px;
    border-bottom: 1px solid var(--line);
    background: #ffffff;
  }}
  h1 {{
    margin: 0 0 8px;
    font-size: 26px;
    line-height: 1.15;
    letter-spacing: 0;
  }}
  .sub {{
    margin: 0;
    max-width: 1050px;
    color: var(--muted);
    line-height: 1.45;
    font-size: 14px;
  }}
  .stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
    gap: 10px;
    padding: 16px 34px 6px;
  }}
  .stat {{
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 12px 13px;
  }}
  .stat strong {{
    display: block;
    font-size: 22px;
    margin-bottom: 3px;
  }}
  .stat span {{
    color: var(--muted);
    font-size: 12px;
  }}
  nav {{
    display: flex;
    gap: 8px;
    padding: 16px 34px 10px;
    flex-wrap: wrap;
  }}
  button {{
    border: 1px solid var(--line);
    background: #ffffff;
    color: var(--ink);
    border-radius: 7px;
    padding: 9px 12px;
    font-weight: 700;
    cursor: pointer;
  }}
  button.active {{
    background: var(--accent);
    border-color: var(--accent);
    color: #ffffff;
  }}
  main {{ padding: 0 34px 34px; }}
  section.view {{ display: none; }}
  section.view.active {{ display: block; }}
  .toolbar {{
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin: 10px 0 12px;
    color: var(--muted);
    font-size: 13px;
  }}
  .toolbar label {{
    display: inline-flex;
    gap: 6px;
    align-items: center;
    white-space: nowrap;
  }}
  .graph-frame {{
    overflow: auto;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: #ffffff;
  }}
  .graph-frame svg {{
    display: block;
    max-width: none;
  }}
  .graph-frame .node.dimmed,
  .graph-frame .edge.dimmed {{
    opacity: .08;
  }}
  .two-col {{
    display: grid;
    grid-template-columns: minmax(250px, 340px) 1fr;
    gap: 14px;
    align-items: start;
  }}
  .panel {{
    background: #ffffff;
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 14px;
  }}
  h2 {{
    font-size: 17px;
    margin: 0 0 9px;
  }}
  ul {{
    margin: 0;
    padding-left: 18px;
    color: var(--muted);
    line-height: 1.45;
    font-size: 13px;
  }}
  input[type="search"] {{
    width: min(520px, 100%);
    border: 1px solid var(--line);
    border-radius: 7px;
    padding: 10px 11px;
    font-size: 14px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    background: #ffffff;
    border: 1px solid var(--line);
    border-radius: 8px;
    overflow: hidden;
    font-size: 12px;
  }}
  th, td {{
    padding: 8px 9px;
    border-bottom: 1px solid var(--line);
    text-align: left;
    vertical-align: top;
  }}
  th {{
    background: #edf1ef;
    font-size: 11px;
    color: #354149;
  }}
  .downloads {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
    gap: 10px;
  }}
  .downloads a {{
    display: block;
    padding: 12px 13px;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: #ffffff;
    color: var(--accent);
    font-weight: 700;
    text-decoration: none;
  }}
  @media (max-width: 820px) {{
    header, .stats, nav, main {{ padding-left: 16px; padding-right: 16px; }}
    .two-col {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
<header>
  <h1>Free Full Graph Pack: Metaverse-Crypto Financial Crime Environments</h1>
  <p class="sub">This is a standalone local file. It uses the Round 5 topic-model themes, the local Qwen evidence extraction, and the 59-document corpus evidence table to model, analyse, and identify intervention points. No paid service, no Zep Cloud, no external JavaScript library.</p>
</header>
<div class="stats">{stats_html}</div>
<nav>
  <button class="active" data-view="semantic">Topic to Intervention Graph</button>
  <button data-view="document">Full Document Evidence Graph</button>
  <button data-view="lifecycle">Lifecycle Intervention Map</button>
  <button data-view="table">Evidence Table</button>
  <button data-view="files">Export Files</button>
</nav>
<main>
  <section class="view active" id="semantic">
    <div class="toolbar">{type_html}</div>
    <div class="graph-frame">{semantic_svg}</div>
  </section>
  <section class="view" id="document">
    <div class="toolbar">Every corpus document is included; document circles are scaled by evidence score.</div>
    <div class="graph-frame">{document_svg}</div>
  </section>
  <section class="view" id="lifecycle">
    <div class="graph-frame">{lifecycle_svg}</div>
  </section>
  <section class="view" id="table">
    <div class="toolbar"><input id="docSearch" type="search" placeholder="Search documents, relevance labels, or document IDs"></div>
    <table>
      <thead><tr><th>Doc</th><th>Title</th><th>Score</th><th>Relevance</th><th>Threat links</th><th>Evidence dimensions</th></tr></thead>
      <tbody id="docRows">{''.join(top_doc_rows)}</tbody>
    </table>
  </section>
  <section class="view" id="files">
    <div class="two-col">
      <div class="panel">
        <h2>Graph Relations</h2>
        <ul>{relation_html}</ul>
      </div>
      <div class="panel">
        <h2>Included Exports</h2>
        <div class="downloads">
          <a href="topic_threat_intervention_full.svg">Static topic-to-intervention SVG</a>
          <a href="document_evidence_network_full.svg">Static document evidence SVG</a>
          <a href="intervention_lifecycle_map.svg">Lifecycle SVG</a>
          <a href="graph_data.json">Graph JSON</a>
          <a href="graph_nodes.csv">Nodes CSV</a>
          <a href="graph_edges.csv">Edges CSV</a>
          <a href="graph_data.graphml">GraphML for Gephi/yEd</a>
          <a href="intervention_matrix.csv">Intervention matrix CSV</a>
        </div>
      </div>
    </div>
  </section>
</main>
<script id="graphData" type="application/json">{safe_graph_json}</script>
<script>
  const buttons = [...document.querySelectorAll('nav button')];
  const views = [...document.querySelectorAll('.view')];
  buttons.forEach(button => {{
    button.addEventListener('click', () => {{
      buttons.forEach(b => b.classList.toggle('active', b === button));
      views.forEach(v => v.classList.toggle('active', v.id === button.dataset.view));
    }});
  }});
  document.querySelectorAll('[data-type-toggle]').forEach(input => {{
    input.addEventListener('change', () => {{
      const type = input.dataset.typeToggle;
      document.querySelectorAll('.graph-frame .node[data-type="' + type + '"]').forEach(n => n.classList.toggle('dimmed', !input.checked));
    }});
  }});
  const search = document.getElementById('docSearch');
  if (search) {{
    search.addEventListener('input', () => {{
      const q = search.value.trim().toLowerCase();
      document.querySelectorAll('#docRows tr').forEach(row => {{
        row.style.display = !q || row.dataset.search.includes(q) ? '' : 'none';
      }});
    }});
  }}
</script>
</body>
</html>"""


def write_readme(docs: list[dict], nodes: list[dict], edges: list[dict]) -> None:
    doc_counts = Counter()
    for d in docs:
        for tid, _ in d["top_threats"]:
            doc_counts[tid] += 1
    threat_lines = []
    threat_lookup = {t["id"]: t["label"] for t in THREATS}
    for tid, count in doc_counts.most_common():
        threat_lines.append(f"- {threat_lookup.get(tid, tid)}: {count} linked documents")

    readme = f"""# Free Full Graph Pack

This graph pack was generated entirely locally from the existing Round 5 outputs:

- Source evidence table: `{EVIDENCE_CSV}`
- Document count: {len(docs)}
- Nodes: {len(nodes)}
- Edges: {len(edges)}
- Cost boundary: no paid API, no Zep Cloud, and no external web libraries.

## Main files

- `full_interactive_graph_pack.html` - standalone browser graph pack with three graph views.
- `topic_threat_intervention_full.svg` - static topic-model to intervention graph.
- `document_evidence_network_full.svg` - static network containing all 59 documents.
- `intervention_lifecycle_map.svg` - lifecycle map of modelling, analysis, and intervention points.
- `graph_data.json` - complete node/edge graph data.
- `graph_nodes.csv` and `graph_edges.csv` - tabular export for audit or reuse.
- `graph_data.graphml` - importable into free graph tools such as Gephi or yEd.
- `intervention_matrix.csv` - threat-to-signal-to-intervention matrix.

## Most connected threat environments

{chr(10).join(threat_lines)}

## Interpretation note

The graph is an analytical model, not a claim that every document proves every threat. Document-to-threat edges are generated from the extracted title and evidence snippets using transparent local keyword rules, while the topic-to-threat structure follows the verified Round 5 topic-model labels and prevalence values.
"""
    (PACK_DIR / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    docs = load_documents()
    nodes, edges = build_graph(docs)

    graph_data = {
        "created_by": "Codex local/free graph builder",
        "cost_boundary": "No paid API, no Zep Cloud, no external web libraries.",
        "source_evidence_table": str(EVIDENCE_CSV),
        "summary": {
            "documents": len(docs),
            "nodes": len(nodes),
            "edges": len(edges),
            "topics": len(TOPICS),
            "threat_environments": len(THREATS),
            "interventions": len(INTERVENTIONS),
        },
        "topics": TOPICS,
        "threats": THREATS,
        "layers": LAYERS,
        "signals": SIGNALS,
        "interventions": INTERVENTIONS,
        "nodes": nodes,
        "edges": edges,
    }
    (PACK_DIR / "graph_data.json").write_text(json.dumps(graph_data, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csvs(nodes, edges)
    write_graphml(nodes, edges)
    write_intervention_matrix(nodes, edges)

    semantic_svg = make_semantic_svg(nodes, edges)
    document_svg = make_document_svg(nodes, edges, docs)
    lifecycle_svg = make_lifecycle_svg()
    (PACK_DIR / "topic_threat_intervention_full.svg").write_text(semantic_svg, encoding="utf-8")
    (PACK_DIR / "document_evidence_network_full.svg").write_text(document_svg, encoding="utf-8")
    (PACK_DIR / "intervention_lifecycle_map.svg").write_text(lifecycle_svg, encoding="utf-8")
    (PACK_DIR / "full_interactive_graph_pack.html").write_text(
        make_html(nodes, edges, docs, semantic_svg, document_svg, lifecycle_svg),
        encoding="utf-8",
    )
    write_readme(docs, nodes, edges)

    print(json.dumps(graph_data["summary"], indent=2))
    print(str(PACK_DIR))


if __name__ == "__main__":
    main()
