#!/usr/bin/env python3
"""Informational, bounded semantic check of keyword-rule document->threat edges.

Mechanism of the rule edges (02_build_graph_k11_65docs.py, load_documents): for each
publication, count THREATS[*].keywords in its file name + relevance label + up to three evidence
snippets; keep the top three threats. Topics play no part in this.

To relate those edges to the authors' reviewed topic-threat pairs this script uses ONE
analyst-chosen convention, stated here so it is not mistaken for part of the graph rule:
a publication is assigned to the topic with the highest weight in document_topic_matrix.csv
(argmax, no threshold; ties are reported). A rule edge (doc -> threat) is then listed when
(dominant topic, threat) is one of the 10 pairs the authors did not retain. This is a
descriptive cross-tabulation of two different relations (keyword match vs author-reviewed
thematic association). It does not create, delete or re-score any edge, and the listed
document edges do not generate topic edges.

Outputs: validation/rule_layer_vs_approved_mapping.json, validation/rule_edges_in_excluded_pairs.csv
"""
import argparse, csv, json, sys
from collections import Counter, defaultdict
import os
from pathlib import Path
sys.dont_write_bytecode = True
SUPP = Path(os.environ["CHBR_SYNC_ROOT"]) / "incoming" / "Electronic_Supplement_A1" / "tables"
RULE_REL = "document-keyword-matches-threat"

ap = argparse.ArgumentParser(); ap.add_argument("--root", required=True); a = ap.parse_args()
root = Path(a.root)
g = json.loads((root / "graph_pack/graph_data.json").read_text(encoding="utf-8"))
nodes = {n["id"]: n for n in g["nodes"]}
with (SUPP / "document_topic_matrix.csv").open(encoding="utf-8-sig", newline="") as f:
    dtm = {r["document_id"]: {k: float(v) for k, v in r.items() if k.startswith("T")} for r in csv.DictReader(f)}
ties = [d for d, w in dtm.items() if sorted(w.values())[-1] == sorted(w.values())[-2]]
dom = {d: max(w, key=w.get) for d, w in dtm.items()}
recs = json.loads((root / "decisions/k11_topic_threat_decisions_34.json").read_text(encoding="utf-8"))["records"]
excl = {(r["topic_id"], r["threat_id"]): r["joint_decision"] for r in recs if not r["retained"]}
appr = {(r["topic_id"], r["threat_id"]) for r in recs if r["retained"]}
res = Counter(); detail = defaultdict(list); rows = []; tot = 0
for e in g["edges"]:
    if e["relation"] != RULE_REL:
        continue
    tot += 1
    d = nodes[e["source"]]["source_doc_id"]; k = (dom[d], e["target"])
    if k in appr: res["dominant_topic_pair_is_author_retained"] += 1
    elif k in excl:
        res["dominant_topic_pair_is_author_excluded:" + excl[k]] += 1; detail[f"{k[0]}>{k[1]}"].append(d)
        rows.append({"DOC_ID": d, "doc_index": nodes[e["source"]]["doc_index"], "dominant_topic": k[0],
                     "dominant_topic_weight": round(dtm[d][k[0]], 4), "threat": e["target"],
                     "keyword_matches": e.get("count", ""), "author_decision_for_topic_threat_pair": excl[k],
                     "note": "keyword-rule document edge only; no topic-threat edge is created from it"})
    else: res["dominant_topic_pair_not_among_the_34_reviewed_pairs"] += 1
rows.sort(key=lambda r: (r["dominant_topic"], r["threat"], r["DOC_ID"]))
with (root / "validation/rule_edges_in_excluded_pairs.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
out = {"n_keyword_rule_doc_threat_edges": tot, "dominant_topic_rule": "argmax of document_topic_matrix row; no threshold",
       "documents_with_tied_top_weight": ties,
       "summary": dict(sorted(res.items())),
       "n_edges_listed_in_excluded_pairs": len(rows),
       "excluded_pair_hits_by_pair": {k: len(v) for k, v in sorted(detail.items())},
       "author_in_degree_by_threat_from_24_approved_edges": dict(Counter(e["target"] for e in g["edges"] if e["edge_origin"] == "author_reviewed_k11_20261001").most_common()),
       "keyword_rule_in_degree_by_threat": dict(Counter(e["target"] for e in g["edges"] if e["relation"] == RULE_REL).most_common()),
       "dominant_topic_doc_counts": dict(sorted(Counter(dom.values()).items()))}
(root / "validation/rule_layer_vs_approved_mapping.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
