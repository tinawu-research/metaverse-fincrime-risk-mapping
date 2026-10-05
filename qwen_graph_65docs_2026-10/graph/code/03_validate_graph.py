#!/usr/bin/env python3
"""Validate a generated K=11 / 65-publication graph pack.

Usage: 03_validate_graph.py --root <graph_65docs_k11_*> [--pack graph_pack] [--figures figures]
Writes <root>/validation/validation_report.json and prints PASS/FAIL lines. Exit 1 on any FAIL.
Read-only with respect to the old code and the original analysis products.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
import os
from pathlib import Path

sys.dont_write_bytecode = True

ROOT_SYNC = Path(os.environ["CHBR_SYNC_ROOT"])
OLD_SCRIPT = Path(os.environ["CHBR_OLD_REPO_ROOT"]) / "code" / "05_build_free_graph_pack.py"
SUPP = ROOT_SYNC / "incoming" / "Electronic_Supplement_A1" / "tables"
AUTHOR = "author_reviewed_k11_20261001"


def load_mod(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_csv(p: Path):
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--pack", default="graph_pack")
    ap.add_argument("--figures", default="figures")
    ap.add_argument("--report", default="validation/validation_report.json")
    args = ap.parse_args()
    root = Path(args.root)
    pack = root / args.pack
    fig = root / args.figures
    code = root / "code"

    results = []

    def check(name, ok, detail=""):
        results.append({"check": name, "pass": bool(ok), "detail": detail})

    g = json.loads((pack / "graph_data.json").read_text(encoding="utf-8"))
    nodes, edges = g["nodes"], g["edges"]
    nid = {n["id"] for n in nodes}
    ntype = {n["id"]: n["type"] for n in nodes}

    # ---- A. compatibility with the old implementation's full definitions ---------------
    old = load_mod(OLD_SCRIPT, "old_graph_script")
    new = load_mod(code / "02_build_graph_k11_65docs.py", "new_graph_script")
    for attr in ("THREATS", "LAYERS", "SIGNALS", "INTERVENTIONS", "DIMENSIONS", "TYPE_COLOR"):
        check(f"definition_identical_to_old:{attr}", getattr(old, attr) == getattr(new, attr))
    check("threat_ids_in_graph_equal_old_THREATS", {n for n in nid if n.startswith("TH_")} == {t["id"] for t in old.THREATS})
    old_threat_ids = {t["id"] for t in old.THREATS}
    dec = json.loads((root / "decisions/k11_topic_threat_decisions_34.json").read_text(encoding="utf-8"))
    check("every_reviewed_pair_threat_code_exists_in_old_THREATS", all(r["threat_id"] in old_threat_ids for r in dec["records"]))

    # ---- B. 65-publication identity ----------------------------------------------------------
    manifest_ids = {r["document_id"] for r in read_csv(SUPP / "corpus_manifest.csv")}
    doc_nodes = [n for n in nodes if n["type"] == "document"]
    check("65_document_nodes", len(doc_nodes) == 65, len(doc_nodes))
    check("document_node_source_ids_equal_manifest_65", {n["source_doc_id"] for n in doc_nodes} == manifest_ids)
    check("document_node_ids_unique", len({n["id"] for n in doc_nodes}) == 65)
    ev_ids = {r["doc_id"] for r in read_csv(ROOT_SYNC / "qwen_65docs/preflight/document_evidence_table_65.csv")}
    check("document_nodes_equal_rule_output_ids", {n["source_doc_id"] for n in doc_nodes} == ev_ids)
    check("calvo_removed_document_absent", not any("D037" in n["id"] or "Calvo" in n.get("title", "") for n in doc_nodes))

    # ---- C. the 24 approved relations ------------------------------------------------------
    approved = {(r["topic_id"], r["threat_id"]) for r in read_csv(root / "decisions/k11_approved_edges_24.csv")}
    check("approved_set_has_24", len(approved) == 24)
    tt_edges = [e for e in edges if ntype.get(e["source"]) == "topic" and ntype.get(e["target"]) == "threat"]
    tt_set = {(e["source"], e["target"]) for e in tt_edges}
    check("topic_threat_edges_exactly_the_24_approved", tt_set == approved and len(tt_edges) == 24,
          f"extra={sorted(tt_set - approved)} missing={sorted(approved - tt_set)}")
    check("all_topic_threat_edges_flagged_author_origin", all(e.get("edge_origin") == AUTHOR for e in tt_edges))
    check("author_origin_edges_only_topic_threat", all(ntype[e["source"]] == "topic" and ntype[e["target"]] == "threat"
                                                       for e in edges if e.get("edge_origin") == AUTHOR))
    excluded = {(r["topic_id"], r["threat_id"]) for r in dec["records"] if not r["retained"]}
    check("ten_excluded_pairs", len(excluded) == 10)
    check("none_of_10_excluded_pairs_in_graph_any_direction",
          not any((e["source"], e["target"]) in excluded or (e["target"], e["source"]) in excluded for e in edges),
          sorted(excluded & tt_set))
    leave = {(r["topic_id"], r["threat_id"]) for r in dec["records"] if r["joint_decision"] == "Leave conceptual"}
    check("four_leave_conceptual_absent", len(leave) == 4 and not (leave & tt_set))
    topic_ids = [n["id"] for n in nodes if n["type"] == "topic"]
    check("11_topic_nodes", sorted(topic_ids) == [f"T{i:02d}" for i in range(1, 12)])
    check("T03_node_present", "T03" in nid)
    check("T03_has_no_edges_at_all", not any(e["source"] == "T03" or e["target"] == "T03" for e in edges))
    check("topics_have_only_outgoing_topic_threat_edges",
          all(ntype[e["source"]] == "topic" or ntype[e["target"]] != "topic" for e in edges)
          and all(ntype[e["target"]] != "topic" for e in edges))
    per_topic = Counter(e["source"] for e in tt_edges)
    expect = {"T01": 1, "T02": 4, "T04": 1, "T05": 3, "T06": 1, "T07": 1, "T08": 4, "T09": 1, "T10": 2, "T11": 6}
    check("per_topic_link_counts_match_guide", dict(per_topic) == expect, dict(per_topic))
    check("9_threat_nodes", len([n for n in nodes if n["type"] == "threat"]) == 9)

    # prevalence
    prev = {n["id"]: n["prevalence"] for n in nodes if n["type"] == "topic"}
    check("prevalence_sums_to_100_at_2dp", abs(sum(prev.values()) - 100.0) < 0.06, sum(prev.values()))

    # keyword-rule document edges are a separate relation family
    check("no_edge_between_document_and_topic_nodes",
          not any({ntype[e["source"]], ntype[e["target"]]} == {"document", "topic"} for e in edges))
    check("keyword_rule_threat_edges_never_author_origin_and_never_topic_endpoint",
          all(e["edge_origin"] == "rule_65docs" and ntype[e["source"]] == "document" and ntype[e["target"]] == "threat"
              for e in edges if e["relation"] in {"document-keyword-matches-threat", "high-score-keyword-anchor"}))
    author_indeg = Counter(e["target"] for e in tt_edges)
    approved_indeg = Counter(t for _, t in approved)
    check("author_threat_ranking_depends_only_on_the_24_approved_edges", author_indeg == approved_indeg, dict(author_indeg))
    fig_src = (code / "04_make_paper_figures.py").read_text(encoding="utf-8")
    check("paper_figure_script_draws_only_author_origin_edges",
          'e.get("edge_origin") == "author_reviewed_k11_20261001"' in fig_src and "document-keyword" not in fig_src)

    # ---- D. structural integrity -------------------------------------------------------------
    dangling = [e for e in edges if e["source"] not in nid or e["target"] not in nid]
    check("no_dangling_edges", not dangling, dangling[:3])
    keys = [(e["source"], e["target"], e["relation"]) for e in edges]
    dup = [k for k, c in Counter(keys).items() if c > 1]
    check("no_duplicate_edges_same_source_target_relation", not dup, dup[:5])
    check("no_self_loops", not [e for e in edges if e["source"] == e["target"]])
    pairs = Counter((e["source"], e["target"]) for e in edges)
    multi = sorted(k for k, c in pairs.items() if c > 1)
    multi_rel = {k: sorted(e["relation"] for e in edges if (e["source"], e["target"]) == k) for k in multi}
    check("multi_relation_pairs_are_only_the_rule_anchor_overlays",
          all(set(v) == {"document-keyword-matches-threat", "high-score-keyword-anchor"} for v in multi_rel.values()),
          {f"{a}>{b}": v for (a, b), v in multi_rel.items()})
    check("every_edge_has_origin", all(e.get("edge_origin") in {AUTHOR, "rule_65docs", "legacy_fixed_concept"} for e in edges))
    isolated = sorted(n for n in nid if not any(e["source"] == n or e["target"] == n for e in edges))
    check("only_T03_is_isolated", isolated == ["T03"], isolated)
    check("rule_edges_only_touch_documents",
          all("document" in (ntype[e["source"]], ntype[e["target"]]) for e in edges if e["edge_origin"] == "rule_65docs"))
    check("legacy_edges_never_touch_topic_or_document",
          all(not ({ntype[e["source"]], ntype[e["target"]]} & {"topic", "document"}) for e in edges if e["edge_origin"] == "legacy_fixed_concept"))
    # legacy count is derivable from the unchanged definitions
    exp_legacy = len(old.THREATS) * (2 + 3) + (len(old.LAYERS) - 1) + len(old.SIGNALS) + len(old.INTERVENTIONS)
    check("legacy_edge_count_equals_definitions_minus_self_loop", sum(e["edge_origin"] == "legacy_fixed_concept" for e in edges) == exp_legacy, exp_legacy)

    # ---- E. exports agree with graph_data.json -------------------------------------------------
    ncsv, ecsv = read_csv(pack / "graph_nodes.csv"), read_csv(pack / "graph_edges.csv")
    check("csv_counts_match_json", len(ncsv) == len(nodes) and len(ecsv) == len(edges), f"{len(ncsv)}/{len(ecsv)}")
    check("csv_edge_keys_match_json", Counter((r["source"], r["target"], r["relation"]) for r in ecsv) == Counter(keys))
    ns = "{http://graphml.graphdrawing.org/xmlns}"
    tree = ET.parse(pack / "graph_data.graphml").getroot()
    gm_nodes = tree.findall(f".//{ns}node")
    gm_edges = tree.findall(f".//{ns}edge")
    check("graphml_counts_match_json", len(gm_nodes) == len(nodes) and len(gm_edges) == len(edges), f"{len(gm_nodes)}/{len(gm_edges)}")
    check("graphml_author_edges_24", sum(1 for e in gm_edges if any(d.get("key") == "edge_origin" and d.text == AUTHOR for d in e)) == 24)

    # ---- F. qualifiers travel with the edges ---------------------------------------------------
    byk = {(e["source"], e["target"]): e for e in tt_edges}
    q = lambda k, s: s in byk[k].get("qualifiers", "")
    check("T01_PRIVACY_perception_qualifier", q(("T01", "TH_PRIVACY"), "perception_evidence") and "perception" in byk[("T01", "TH_PRIVACY")]["evidence"].lower())
    check("T06_SCAM_perception_qualifier", q(("T06", "TH_SCAM"), "perception_evidence") and "perceived" in byk[("T06", "TH_SCAM")]["evidence"].lower())
    check("T04_CYBER_trust_reputation_only", q(("T04", "TH_CYBER"), "trust_reputation_system_attacks_only") and "reputation" in byk[("T04", "TH_CYBER")]["evidence"].lower())
    check("T10_CYBER_potential_quantum", q(("T10", "TH_CYBER"), "potential_future_quantum_risk_only") and "potential" in byk[("T10", "TH_CYBER")]["evidence"].lower())
    check("T08_DEFI_manning_nft_finding", q(("T08", "TH_DEFI"), "manning_nft_specific_finding_no_en_masse_switch_p11") and "en masse" in byk[("T08", "TH_DEFI")]["evidence"])
    check("T06_and_T09_both_present_and_unmerged", {"T06", "T09"} <= set(topic_ids) and ("T06", "TH_SCAM") in byk and ("T09", "TH_NFT") in byk)
    check("every_author_edge_has_DOC_IDs_pages_and_status",
          all(e.get("doc_ids") and e.get("pdf_pages") and e.get("source_check") for e in tt_edges))
    check("author_edge_DOC_IDs_all_in_65", all(set(e["doc_ids"].split("; ")) <= manifest_ids for e in tt_edges))

    # ---- G. figures --------------------------------------------------------------------------------
    sem = (pack / "topic_threat_intervention_full.svg").read_text(encoding="utf-8")
    sem_author = len(re.findall(r'data-origin="author_reviewed_k11_20261001"', sem))
    check("semantic_svg_draws_24_author_edges", sem_author == 24, sem_author)
    n_model_edges = sum(1 for e in edges if "document" not in (ntype[e["source"]], ntype[e["target"]]))
    check("semantic_svg_draws_every_non_document_edge", len(re.findall(r'<path class="edge', sem)) == n_model_edges == 24 + exp_legacy,
          f"svg={len(re.findall(r'<path class=\"edge', sem))} expected={n_model_edges}")
    for stem in ("Figure_K11_topic_threat_associations",):
        for ext in ("png", "pdf", "svg"):
            check(f"figure_exists:{stem}.{ext}", (fig / f"{stem}.{ext}").exists() and (fig / f"{stem}.{ext}").stat().st_size > 5000)
    fsvg = (fig / "Figure_K11_topic_threat_associations.svg").read_text(encoding="utf-8")
    for t in expect:
        check(f"figure_svg_labels_{t}", f">{t}<" in fsvg)
    check("figure_svg_labels_T03_no_link_note", "no approved link" in fsvg)
    check("html_pack_mentions_limits", "not estimates of crime incidence" in (pack / "full_interactive_graph_pack.html").read_text(encoding="utf-8")
          or "not estimates of crime incidence" in (pack / "full_interactive_graph_pack.html").read_text(encoding="utf-8").replace("\n", " "))
    html_txt = (pack / "full_interactive_graph_pack.html").read_text(encoding="utf-8")
    check("html_pack_has_no_59_or_Round5_leftovers", "59-document" not in html_txt and "Round 5" not in html_txt and "All 59" not in html_txt)

    summary = {
        "documents": len(doc_nodes), "nodes": len(nodes), "edges": len(edges),
        "nodes_by_type": dict(sorted(Counter(n["type"] for n in nodes).items())),
        "edges_by_origin": dict(sorted(Counter(e["edge_origin"] for e in edges).items())),
        "edges_by_relation": dict(sorted(Counter(e["relation"] for e in edges).items())),
        "multi_relation_pairs": {f"{a}>{b}": v for (a, b), v in multi_rel.items()},
        "approved_topic_threat_edges": len(tt_edges),
    }
    out = {"all_pass": all(r["pass"] for r in results), "n_checks": len(results), "summary": summary, "checks": results}
    rp = root / args.report
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in results:
        print(("PASS " if r["pass"] else "FAIL ") + r["check"] + ("" if r["pass"] else f"  -> {r['detail']}"))
    print(f"\n{sum(r['pass'] for r in results)}/{len(results)} checks passed")
    print(json.dumps(summary, indent=2))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
