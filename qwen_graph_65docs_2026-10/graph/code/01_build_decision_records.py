#!/usr/bin/env python3
"""Step 1 - machine-readable K=11 topic-threat decision records (34 pairs, 24 retained).

Reads (read-only):
  * incoming/K11_Topic_Threat_Decision_Guide 1.md   (source-bearing decision table)
  * incoming/K11_Joint_Review_Checklist 1.md        (compact decision record)
  * incoming/Electronic_Supplement_A1/tables/{topic_prevalence,topic_summary,
    document_topic_matrix,corpus_manifest}.csv      (K=11 LDA record, 65 publications)
  * drive_verified_20260928/label_adjudication.xlsx (adjudicated topic labels)
  * qwen_65docs/preflight/document_evidence_table_65.csv (65-document rule output)

Writes (to --out only):
  decisions/k11_topic_threat_decisions_34.{csv,json}
  decisions/k11_approved_edges_24.csv
  decisions/k11_topics.json              (11 topics: label, prevalence, dominant-doc count)
  decisions/input_consistency_check.json (every cross-check, pass/fail, details)

The per-pair evidence anchors (DOC_ID, physical PDF pages, source-check status) are
curated below from the Decision Guide and are then machine-checked against the Guide
text. The script does not add, promote or re-score any relationship.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, OrderedDict
import os
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(os.environ["CHBR_SYNC_ROOT"])
INCOMING = ROOT / "incoming"
GUIDE = INCOMING / "K11_Topic_Threat_Decision_Guide 1.md"
CHECKLIST = INCOMING / "K11_Joint_Review_Checklist 1.md"
SUPP = INCOMING / "Electronic_Supplement_A1" / "tables"
LABEL_XLSX = ROOT / "drive_verified_20260928" / "label_adjudication.xlsx"
EVIDENCE65 = ROOT / "qwen_65docs" / "preflight" / "document_evidence_table_65.csv"

THREAT_CODES = ["TH_SCAM", "TH_IDENTITY", "TH_NFT", "TH_WALLET", "TH_DEFI",
                "TH_PRIVACY", "TH_PAYMENT", "TH_CYBER", "TH_GOVERNANCE"]

# Source-check status vocabulary (kept deliberately narrow; see report).
AUTH = "author_checked_20261001"                  # Guide marks the anchor "Checked"
TBL = "table_excerpt_author_not_located"          # Guide: passage "reported by Author C's table"
NONE = "no_supporting_passage_supplied"           # nothing to check (Drop / Leave conceptual)
CHK_INSUFF = "author_checked_support_insufficient"  # checked, did not support the category
SERVER_PRIOR = "server_pdf_opened_20260928"       # 09 review table: PDF page opened on server
SERVER_RECHECK = "server_pdf_page_text_rechecked_20261002"  # this round, pdftotext on page

# Names used for readability only (taken from the Guide's own wording).
DOC_NAME = {
    "D7d7f6f621da1": "Hudnurkar et al.", "D24774522d751": "Choksi et al.",
    "Dcb7f93f9aa99": "Su et al.", "D28078c8a10cc": "Zadorozhnyi et al. (Innovative Accounting and Auditing)",
    "D21cf0acb1a9a": "Jurisdictional Challenges in Metaverse (chapter)",
    "Dfed6d84a0e4f": "O'Connor and O'Reilly (Is the metaverse failing)",
    "D1095d64c71c1": "Ryu et al.", "Dfdc0a7ab21ac": "Manning et al.",
    "Db80703b6ee6c": "Shim (Classification of NFT Security Issues and Threats)",
    "D399d99db36b3": "Chao et al.", "D2590938a004e": "Chan et al.",
    "De395cd4ff88c": "Pan et al.", "D74bc17aea3dd": "Malve et al.",
    "D957f80b1f6a0": "Aloudat et al.", "D5279c89a9098": "Yousafzai et al.",
    "D6486a0b043d4": "Bhaskar et al.", "Dc3ba77443e3f": "NFT-avatar privacy awareness framework",
    "D6bbb4f6b30f4": "Awan et al. (Blockchain-based trust management)",
    "De11ad817ca1d": "METAseen", "D569a973fcbb6": "Blockchain-based signature exchange protocol",
    "D1a5520aa7ae7": "Jin and Ryu",
}
INFERRED_DOC_ID_PAIRS = {"T05>TH_CYBER", "T06>TH_NFT", "T04>TH_IDENTITY"}
SERVER_RECHECK_DOCS = {"D28078c8a10cc", "Dfed6d84a0e4f", "Db80703b6ee6c"}


def A(doc, pages, status=AUTH, note=""):
    return {"doc_id": doc, "doc_name": DOC_NAME.get(doc, ""), "physical_pdf_pages": pages,
            "source_check_status": status, "note": note}


# pair -> ordered evidence anchors. Pages are physical PDF pages as stated in the Guide.
EVIDENCE = OrderedDict([
    ("T02>TH_PAYMENT", [A("D7d7f6f621da1", "1; 7-11"), A("D24774522d751", "1")]),
    ("T02>TH_CYBER", [A("Dcb7f93f9aa99", "1")]),
    ("T05>TH_SCAM", [A("D28078c8a10cc", "8", TBL)]),
    ("T05>TH_GOVERNANCE", [A("D28078c8a10cc", "8", TBL), A("D21cf0acb1a9a", "8-9")]),
    ("T06>TH_SCAM", [A("Dfed6d84a0e4f", "6", TBL,
                       "Publisher abstract (exploratory study of NFT resistance) was checked by the authors; the p.6 interview passage was not.")]),
    ("T06>TH_NFT", [A("Dfed6d84a0e4f", "6", TBL, "Guide says 'the same p.6 material' as T06>TH_SCAM; DOC_ID inferred from that.")]),
    ("T07>TH_IDENTITY", [A("D1095d64c71c1", "2")]),
    ("T08>TH_SCAM", [A("Dfdc0a7ab21ac", "3"), A("Db80703b6ee6c", "2", TBL)]),
    ("T08>TH_DEFI", [A("Dfdc0a7ab21ac", "3; 8; 17")]),
    ("T08>TH_GOVERNANCE", [A("D399d99db36b3", "3; 6")]),
    ("T09>TH_NFT", [A("D2590938a004e", "6")]),
    ("T10>TH_PRIVACY", [A("De395cd4ff88c", "1")]),
    ("T11>TH_CYBER", [A("D74bc17aea3dd", "8")]),
    ("T11>TH_IDENTITY", [A("D74bc17aea3dd", "7"), A("D957f80b1f6a0", "1; 4"), A("D5279c89a9098", "27")]),
    ("T11>TH_SCAM", [A("D74bc17aea3dd", "7"), A("D6486a0b043d4", "10")]),
    ("T11>TH_PRIVACY", [A("D74bc17aea3dd", "9")]),
    ("T11>TH_DEFI", [A("D74bc17aea3dd", "8")]),
    ("T11>TH_GOVERNANCE", [A("D74bc17aea3dd", "9")]),
    ("T02>TH_IDENTITY", [A("Dc3ba77443e3f", "2")]),
    ("T02>TH_PRIVACY", [A("Dc3ba77443e3f", "1-2")]),
    ("T04>TH_CYBER", [A("D6bbb4f6b30f4", "1; 12")]),
    ("T04>TH_PAYMENT", [A("", "", CHK_INSUFF, "Guide: checked passages concern general trust/reputation mechanisms; no document/page is cited for a payment-specific attack.")]),
    ("T04>TH_IDENTITY", [A("D6bbb4f6b30f4", "12", CHK_INSUFF, "Guide cites 'p.12' without a DOC_ID; DOC_ID inferred from the T04>TH_CYBER anchor, which cites the same page (p.12, Sybil attack) in D6bbb4f6b30f4.")]),
    ("T05>TH_CYBER", [A("D28078c8a10cc", "8", TBL, "Guide cites only 'the audit excerpt'; document and page taken from the 09 review table (same p.8 passage).")]),
    ("T05>TH_PRIVACY", [A("De11ad817ca1d", "9")]),
    ("T05>TH_DEFI", [A("", "", NONE, "DAO terminology only; no reviewed passage.")]),
    ("T05>TH_IDENTITY", [A("", "", NONE, "Avatar terminology only; no supporting passage supplied.")]),
    ("T05>TH_NFT", [A("", "", NONE, "Asset terminology only; no supporting passage supplied.")]),
    ("T07>TH_DEFI", [A("D569a973fcbb6", "1-5", CHK_INSUFF)]),
    ("T08>TH_WALLET", [A("Dfdc0a7ab21ac", "8 (section 9.1)")]),
    ("T10>TH_WALLET", [A("", "", NONE, "Network terminology only; no reviewed passage.")]),
    ("T10>TH_CYBER", [A("De395cd4ff88c", "1-2")]),
    ("T04>TH_DEFI", [A("D6bbb4f6b30f4", "1", CHK_INSUFF, "Guide: smart contracts described as defensive trust regulators.")]),
    ("T01>TH_PRIVACY", [A("D1a5520aa7ae7", "6-7")]),
])

# Qualifiers that the authors require to travel with specific edges / topics.
QUALIFIER_FLAGS = {
    "T01>TH_PRIVACY": ["perception_evidence", "p8_human_identity_construct_is_not_identity_theft"],
    "T06>TH_SCAM": ["perception_evidence", "interviews_do_not_establish_crimes_or_incidence"],
    "T04>TH_CYBER": ["trust_reputation_system_attacks_only", "no_payment_specific_or_financial_offence_mechanism"],
    "T10>TH_CYBER": ["potential_future_quantum_risk_only", "no_observed_operational_quantum_attacks"],
    "T08>TH_DEFI": ["manning_nft_specific_finding_no_en_masse_switch_p11", "no_adoption_frequency_estimate"],
    "T08>TH_WALLET": ["support_overlaps_T08_DEFI_edge_not_independent", "credential_theft_alone_not_laundering"],
    "T08>TH_SCAM": ["review_case_synthesis_not_new_measurement"],
    "T05>TH_SCAM": ["general_fraud_concern_only", "source_check_limitation_recorded"],
    "T05>TH_PRIVACY": ["metaseen_applications_only_no_legal_violation_claim"],
    "T11>TH_DEFI": ["smart_contract_vulnerability_exploitation_only"],
    "T02>TH_PAYMENT": ["ml_classifier_comparison_not_seven_algorithm_ensemble"],
}

# Source-description rules that attach to topics rather than edges.
TOPIC_NOTES = {
    "T03": "No approved topic-threat link. Insufficient reviewed support, not proof that associated publications lack threat discussion.",
    "T06": "Distinct from T09; not merged (conceptual overlap does not require merging endpoints).",
    "T09": "Distinct from T06; not merged.",
    "T11": "Largest topic (28.18%). Malve et al. has T11 as its own strongest topic (0.6376) but is not the highest-loading T11 document.",
}

TOPIC_ID_RE = re.compile(r"^(T\d{2}) → (TH_[A-Z]+)$")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_md(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    return s.strip()


def parse_tables(path: Path) -> dict:
    """Return {section_heading: [row cells...]} for every markdown table."""
    out: dict[str, list[list[str]]] = {}
    heading, in_table, rows = None, False, []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            if rows:
                out.setdefault(heading, []).extend(rows)
                rows = []
            heading = line.lstrip("# ").strip()
            in_table = False
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue  # separator
            rows.append(cells)
        else:
            if rows:
                out.setdefault(heading, []).extend(rows)
                rows = []
    if rows:
        out.setdefault(heading, []).extend(rows)
    return out


def load_guide_rows(path: Path) -> list[dict]:
    secs = parse_tables(path)
    wanted = [
        "The 18 originally proposed connections — agreed decisions",
        "The 14 originally conceptual/pending candidates — agreed dispositions",
        "The previously removed candidate — agreed disposition",
        "Additional T01 privacy connection — agreed inclusion",
    ]
    recs = []
    for sec in wanted:
        rows = secs[sec]
        assert rows[0][0] == "Pair", (sec, rows[0])
        for r in rows[1:]:
            m = TOPIC_ID_RE.match(strip_md(r[0]))
            assert m, r[0]
            recs.append({
                "pair_key": f"{m.group(1)}>{m.group(2)}", "topic_id": m.group(1), "threat_id": m.group(2),
                "guide_section": sec, "original_status": strip_md(r[1]), "joint_decision": strip_md(r[2]),
                "graph_action": strip_md(r[3]), "guide_evidence_text": strip_md(r[4]),
                "agreed_explanation": strip_md(r[5]), "limits": strip_md(r[6]),
            })
    return recs


def load_checklist_rows(path: Path) -> dict:
    secs = parse_tables(path)
    recs = {}
    for sec, rows in secs.items():
        if not rows or rows[0][0] != "Pair":
            continue
        for r in rows[1:]:
            m = TOPIC_ID_RE.match(strip_md(r[0]))
            assert m, r[0]
            recs[f"{m.group(1)}>{m.group(2)}"] = {
                "original_status": strip_md(r[1]), "joint_decision": strip_md(r[2]),
                "graph_action": strip_md(r[3]), "explanation_and_limits": strip_md(r[4]),
            }
    return recs


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("’", "'")).strip()


def membership_table(path: Path) -> dict:
    rows = parse_tables(path)["Confirmed graph membership"]
    out = {}
    for r in rows[1:]:
        topic = r[0]
        threats = [] if r[3].startswith("None") else [t.strip() for t in r[3].split(",")]
        out[topic] = {"label": r[1], "prevalence_pct": float(r[2].rstrip("%")),
                      "threats": threats, "links": int(r[4])}
    return out


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="graph_65docs_k11_* output directory")
    args = ap.parse_args()
    out = Path(args.out)
    dec_dir = out / "decisions"
    dec_dir.mkdir(parents=True, exist_ok=True)

    checks: list[dict] = []

    def check(name: str, ok: bool, detail="") -> None:
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    # ---- 1. decision records from the Guide, cross-checked with the Checklist ------------
    guide = load_guide_rows(GUIDE)
    cl = load_checklist_rows(CHECKLIST)
    keys = [r["pair_key"] for r in guide]
    check("guide_has_34_unique_pairs", len(keys) == 34 and len(set(keys)) == 34, f"{len(keys)} rows / {len(set(keys))} unique")
    check("checklist_has_34_unique_pairs", len(cl) == 34, f"{len(cl)} rows")
    check("guide_and_checklist_same_pair_set", set(keys) == set(cl))
    check("curated_evidence_covers_same_34_pairs", set(EVIDENCE) == set(keys))

    mismatch = []
    for r in guide:
        c = cl[r["pair_key"]]
        for fld in ("original_status", "joint_decision", "graph_action"):
            if norm(r[fld]) != norm(c[fld]):
                mismatch.append((r["pair_key"], fld, r[fld], c[fld]))
        combined = norm(r["agreed_explanation"] + " " + r["limits"])
        if combined != norm(c["explanation_and_limits"]):
            mismatch.append((r["pair_key"], "explanation_and_limits", combined[:80], norm(c["explanation_and_limits"])[:80]))
    check("guide_vs_checklist_decision_action_explanation_identical", not mismatch, f"{len(mismatch)} mismatches: {mismatch[:3]}")

    decisions = Counter(r["joint_decision"] for r in guide)
    check("decision_counts_match_stated_totals",
          decisions == Counter({"Accept": 13 + 1, "Modify": 4, "Reject": 1, "Promote": 6,
                                "Leave conceptual": 4, "Drop": 5}),
          dict(decisions))  # Accept 13 originally + 1 additional T01; Drop 4 + removed T04>DEFI

    retained_actions = {"Include with stated qualifications"}
    for r in guide:
        r["retained"] = r["graph_action"] in retained_actions
        r["exclusion_class"] = "" if r["retained"] else (
            "leave_conceptual" if r["joint_decision"] == "Leave conceptual" else
            "rejected" if r["joint_decision"] == "Reject" else "dropped")
    n_ret = sum(r["retained"] for r in guide)
    check("24_retained_10_excluded", n_ret == 24 and len(guide) - n_ret == 10, f"{n_ret} retained / {len(guide)-n_ret} excluded")
    excl = Counter(r["exclusion_class"] for r in guide if not r["retained"])
    check("excluded_breakdown_1_reject_4_leave_conceptual_5_drop",
          excl == Counter({"rejected": 1, "leave_conceptual": 4, "dropped": 5}), dict(excl))
    leave = sorted(r["pair_key"] for r in guide if r["joint_decision"] == "Leave conceptual")
    check("four_leave_conceptual_excluded",
          leave == ["T04>TH_IDENTITY", "T05>TH_CYBER", "T05>TH_DEFI", "T07>TH_DEFI"]
          and all(not r["retained"] for r in guide if r["pair_key"] in leave), leave)
    check("original_18_split_13_accept_4_modify_1_reject_17_enter",
          Counter(r["joint_decision"] for r in guide[:18]) == Counter({"Accept": 13, "Modify": 4, "Reject": 1})
          and sum(r["retained"] for r in guide[:18]) == 17)
    check("conceptual_14_split_6_promote_4_leave_4_drop",
          Counter(r["joint_decision"] for r in guide[18:32]) == Counter({"Promote": 6, "Leave conceptual": 4, "Drop": 4}))

    # ---- 2. topics: labels, prevalence, membership table --------------------------------
    mem = membership_table(GUIDE)
    prev_rows = {r["topic"]: r for r in read_csv(SUPP / "topic_prevalence.csv")}
    check("11_topics_in_lda_record", sorted(prev_rows) == [f"T{i:02d}" for i in range(1, 12)])
    prev_ok = all(abs(round(float(prev_rows[t]["percent"]), 2) - mem[t]["prevalence_pct"]) < 1e-9 for t in mem)
    check("prevalence_in_lda_record_equals_guide_membership_table_at_2dp", prev_ok)
    check("prevalence_sums_to_100", abs(sum(float(r["percent"]) for r in prev_rows.values()) - 100.0) < 1e-6)

    import openpyxl  # noqa: E402  (only needed here)
    wb = openpyxl.load_workbook(LABEL_XLSX, data_only=True)
    ws = wb["Reported_agreement"]
    adj_labels = {}
    for row in ws.iter_rows(min_row=2, max_row=12, values_only=True):
        adj_labels[row[0]] = row[5]
    labels_ok = all(adj_labels.get(t) == mem[t]["label"] for t in mem)
    check("labels_in_guide_equal_drive_verified_label_adjudication",
          labels_ok, {t: (adj_labels.get(t), mem[t]["label"]) for t in mem if adj_labels.get(t) != mem[t]["label"]})

    derived_threats = {t: [r["threat_id"] for r in guide if r["retained"] and r["topic_id"] == t] for t in mem}
    mem_ok = all(sorted(derived_threats[t]) == sorted(mem[t]["threats"]) and len(derived_threats[t]) == mem[t]["links"] for t in mem)
    check("retained_pairs_equal_guide_membership_table_per_topic", mem_ok,
          {t: (sorted(derived_threats[t]), sorted(mem[t]["threats"])) for t in mem if sorted(derived_threats[t]) != sorted(mem[t]["threats"])})
    check("T03_has_no_retained_pair", derived_threats["T03"] == [] and not any(r["topic_id"] == "T03" for r in guide))
    check("ten_topics_mapped", sum(1 for t in derived_threats if derived_threats[t]) == 10)
    check("all_threat_codes_known", all(r["threat_id"] in THREAT_CODES for r in guide))

    # ---- 3. 65-publication identity ------------------------------------------------------
    manifest = read_csv(SUPP / "corpus_manifest.csv")
    ids_manifest = [r["document_id"] for r in manifest]
    dtm = read_csv(SUPP / "document_topic_matrix.csv")
    ids_dtm = [r["document_id"] for r in dtm]
    ev = read_csv(EVIDENCE65)
    ids_ev = [r["doc_id"] for r in ev]
    check("65_ids_manifest_matrix_rule_output_identical",
          len(ids_manifest) == len(set(ids_manifest)) == 65 and set(ids_manifest) == set(ids_dtm) == set(ids_ev)
          and len(ids_dtm) == 65 and len(ids_ev) == 65,
          f"manifest={len(ids_manifest)} matrix={len(ids_dtm)} rule_output={len(ids_ev)}")
    check("manifest_all_status_included", all(r["status"] == "included" for r in manifest))
    fn_match = all({r["document_id"]: r["filename"] for r in manifest}[r["doc_id"]] == r["filename"] for r in ev)
    check("rule_output_filenames_equal_manifest_filenames", fn_match)
    anchor_docs = {a["doc_id"] for k in EVIDENCE for a in EVIDENCE[k] if a["doc_id"]}
    check("all_anchor_DOC_IDs_are_in_the_65", anchor_docs <= set(ids_manifest),
          sorted(anchor_docs - set(ids_manifest)))

    # ---- 4. Guide numeric claims against the document-topic matrix -----------------------
    w = {r["document_id"]: {t: float(r[t]) for t in mem} for r in dtm}
    claims = [
        ("T02 weight D c3ba = 0.5940", round(w["Dc3ba77443e3f"]["T02"], 4) == 0.5940),
        ("T04 weight D6bbb = 0.3366 and highest T04 doc", round(w["D6bbb4f6b30f4"]["T04"], 4) == 0.3366 and max(w, key=lambda d: w[d]["T04"]) == "D6bbb4f6b30f4"),
        ("T05 METAseen 0.6164 highest", round(w["De11ad817ca1d"]["T05"], 4) == 0.6164 and max(w, key=lambda d: w[d]["T05"]) == "De11ad817ca1d"),
        ("T05 audit paper 0.5273 second", round(w["D28078c8a10cc"]["T05"], 4) == 0.5273 and sorted(w, key=lambda d: -w[d]["T05"])[1] == "D28078c8a10cc"),
        ("T05 jurisdiction chapter 0.5024 third", round(w["D21cf0acb1a9a"]["T05"], 4) == 0.5024 and sorted(w, key=lambda d: -w[d]["T05"])[2] == "D21cf0acb1a9a"),
        ("T11 Malve own strongest topic 0.6376", round(w["D74bc17aea3dd"]["T11"], 4) == 0.6376 and max(w["D74bc17aea3dd"], key=w["D74bc17aea3dd"].get) == "T11"),
        ("T11 Malve not highest T11 doc (>=4 docs higher)", sum(1 for d in w if w[d]["T11"] > w["D74bc17aea3dd"]["T11"]) >= 4),
        ("T01 Jin and Ryu weight 0.4712", round(w["D1a5520aa7ae7"]["T01"], 4) == 0.4712),
    ]
    for name, ok in claims:
        check("guide_claim:" + name, ok)
    higher = sum(1 for d in w if w[d]["T11"] > w["D74bc17aea3dd"]["T11"])
    dom = Counter(max(w[d], key=w[d].get) for d in w)
    check("dominant_doc_counts_equal_lda_record",
          all(dom.get(t, 0) == int(prev_rows[t]["dominant_document_count"]) for t in prev_rows), dict(dom))

    # ---- 5. anchor consistency with the Guide text ----------------------------------------
    id_re = re.compile(r"\bD[0-9a-f]{12}\b")
    anchor_issues = []
    for r in guide:
        text_ids = set(id_re.findall(r["guide_evidence_text"]))
        cur_ids = {a["doc_id"] for a in EVIDENCE[r["pair_key"]] if a["doc_id"]}
        # These three rows do not name the DOC_ID in the Guide; the curated anchor carries
        # an explicit 'inferred' note (see EVIDENCE) instead of silently filling it in.
        if r["pair_key"] in INFERRED_DOC_ID_PAIRS:
            assert any("inferred" in a["note"] or "09 review table" in a["note"] for a in EVIDENCE[r["pair_key"]])
            continue
        if text_ids != cur_ids:
            anchor_issues.append((r["pair_key"], sorted(text_ids ^ cur_ids)))
    check("curated_anchor_DOC_IDs_equal_DOC_IDs_named_in_guide_row", not anchor_issues, anchor_issues)

    # ---- assemble records --------------------------------------------------------------
    records = []
    for r in guide:
        anchors = []
        for a in EVIDENCE[r["pair_key"]]:
            a = dict(a)
            a["server_check_trail"] = []
            if a["doc_id"] in SERVER_RECHECK_DOCS:
                a["server_check_trail"] = [SERVER_PRIOR, SERVER_RECHECK]
            anchors.append(a)
        author_checked = [a for a in anchors if a["source_check_status"] in (AUTH, CHK_INSUFF)]
        table_only = [a for a in anchors if a["source_check_status"] == TBL]
        if not anchors or all(a["source_check_status"] == NONE for a in anchors):
            pair_status = "no_passage_to_check"
        elif table_only and not author_checked:
            pair_status = "table_excerpt_only_author_could_not_locate_pdf"
        elif table_only:
            pair_status = "mixed_author_checked_plus_table_excerpt"
        else:
            pair_status = "author_checked_this_round"
        records.append({
            "pair_key": r["pair_key"], "topic_id": r["topic_id"], "threat_id": r["threat_id"],
            "original_status": r["original_status"], "joint_decision": r["joint_decision"],
            "graph_action": r["graph_action"], "retained": r["retained"],
            "exclusion_class": r["exclusion_class"],
            "agreed_explanation": r["agreed_explanation"], "limits": r["limits"],
            "qualifier_flags": QUALIFIER_FLAGS.get(r["pair_key"], []),
            "evidence_anchors": anchors, "pair_source_check_status": pair_status,
            "guide_evidence_text": r["guide_evidence_text"],
            "source": "K11_Topic_Threat_Decision_Guide 1.md (cross-checked with K11_Joint_Review_Checklist 1.md)",
        })

    topics = []
    for t in sorted(mem):
        p = prev_rows[t]
        topics.append({"topic_id": t, "label": mem[t]["label"], "prevalence_pct_2dp": mem[t]["prevalence_pct"],
                       "mean_document_prevalence": float(p["mean_document_prevalence"]),
                       "dominant_document_count": int(p["dominant_document_count"]),
                       "approved_threats": derived_threats[t], "approved_link_count": len(derived_threats[t]),
                       "note": TOPIC_NOTES.get(t, "")})

    # ---- write -----------------------------------------------------------------------------
    def flat(rec: dict) -> dict:
        a = rec["evidence_anchors"]
        return {
            "pair_key": rec["pair_key"], "topic_id": rec["topic_id"], "threat_id": rec["threat_id"],
            "original_status": rec["original_status"], "joint_decision": rec["joint_decision"],
            "graph_action": rec["graph_action"], "retained_in_graph": "yes" if rec["retained"] else "no",
            "exclusion_class": rec["exclusion_class"],
            "DOC_IDs": "; ".join(x["doc_id"] for x in a if x["doc_id"]),
            "physical_pdf_pages": "; ".join(f"{x['doc_id'] or '-'}:{x['physical_pdf_pages'] or '-'}" for x in a),
            "source_check_status_per_anchor": "; ".join(f"{x['doc_id'] or '-'}={x['source_check_status']}" for x in a),
            "pair_source_check_status": rec["pair_source_check_status"],
            "agreed_explanation": rec["agreed_explanation"], "limits": rec["limits"],
            "qualifier_flags": "; ".join(rec["qualifier_flags"]),
        }

    cols = list(flat(records[0]).keys())
    with (dec_dir / "k11_topic_threat_decisions_34.csv").open("w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=cols)
        wr.writeheader()
        for rec in records:
            wr.writerow(flat(rec))
    approved = [rec for rec in records if rec["retained"]]
    with (dec_dir / "k11_approved_edges_24.csv").open("w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=cols)
        wr.writeheader()
        for rec in sorted(approved, key=lambda r: (r["topic_id"], r["threat_id"])):
            wr.writerow(flat(rec))
    (dec_dir / "k11_topic_threat_decisions_34.json").write_text(
        json.dumps({"n_pairs_reviewed": 34, "n_retained": 24, "n_excluded": 10,
                    "decision_date": "2026-10-01",
                    "decision_provenance": "Reviewer A confirmed agreement with all recommendations on behalf of themself and Reviewer B, 1 October 2026 (as recorded in the Guide and Checklist).",
                    "records": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    (dec_dir / "k11_topics.json").write_text(json.dumps(topics, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "inputs": {p.name: sha256(p) for p in [GUIDE, CHECKLIST, SUPP / "topic_prevalence.csv", SUPP / "document_topic_matrix.csv",
                                               SUPP / "corpus_manifest.csv", LABEL_XLSX, EVIDENCE65]},
        "all_checks_pass": all(c["pass"] for c in checks), "n_checks": len(checks), "checks": checks,
    }
    (dec_dir / "input_consistency_check.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    for c in checks:
        print(("PASS " if c["pass"] else "FAIL ") + c["check"] + ("" if c["pass"] else f"  -> {c['detail']}"))
    print(f"\n{sum(c['pass'] for c in checks)}/{len(checks)} checks passed")
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
