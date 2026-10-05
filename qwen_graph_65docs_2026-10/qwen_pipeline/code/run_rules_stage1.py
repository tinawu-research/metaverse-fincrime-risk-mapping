#!/usr/bin/env python3
"""
run_rules_stage1.py  --  Stage (1) rule counting for the preflight (handover section 7.2, second paragraph).

Imports the EXISTING analysis script by path, without modifying it, and replays only the deterministic part of
its main() (package copy lines 328-355):
    read input -> parse_documents -> analyse_document -> evidence_score -> sort by doc_id
    -> aggregate stats -> write_csv / document_evidence.json / manifest.json
The Qwen part of main() (ollama_generate, batches, final synthesis, report) is NOT executed. No network call is
made. Nothing is written outside --out-dir.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import platform
import socket
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_module(script: Path):
    sys.dont_write_bytecode = True  # never leave a __pycache__ next to the read-only analysis script
    spec = importlib.util.spec_from_file_location("qwen_stage1_module", str(script))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # top level only defines constants and functions
    for name in ("parse_documents", "analyse_document", "write_csv", "LEXICONS", "QUESTION", "MODEL"):
        if not hasattr(mod, name):
            raise SystemExit(f"script lacks expected symbol: {name}")
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True, help="path to 01_local_qwen_metaverse_fincrime_analysis.py (read only)")
    ap.add_argument("--input", required=True, help="concatenated DOC_ID/FILENAME/PAGES/EXTRACTED_WORDS text file")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--suffix", default="", help="e.g. _65 -> document_evidence_table_65.csv")
    a = ap.parse_args()

    script = Path(a.script)
    input_file = Path(a.input)
    out_dir = Path(a.out_dir)
    if not input_file.exists():
        raise FileNotFoundError(input_file)
    out_dir.mkdir(parents=True, exist_ok=True)

    mod = load_module(script)
    started = dt.datetime.now().isoformat(timespec="seconds")

    # ---- verbatim replay of the deterministic portion of main() ----
    corpus = input_file.read_text(encoding="utf-8", errors="replace")
    documents = mod.parse_documents(corpus)
    analyses = [mod.analyse_document(doc) for doc in documents]

    for item in analyses:
        item["evidence_score"] = sum(item["category_totals"].values())
    analyses.sort(key=lambda item: item["doc_id"])

    aggregate_stats = {
        "input_file": str(input_file),
        "input_size_bytes": input_file.stat().st_size,
        "document_count": len(analyses),
        "total_extracted_words_reported": sum(int(x["extracted_words"] or 0) for x in analyses if str(x["extracted_words"]).isdigit()),
        "category_totals": {
            category: sum(item["category_totals"][category] for item in analyses)
            for category in mod.LEXICONS
        },
        "relevance_counts": {},
        "analysis_question": mod.QUESTION,
        "model": mod.MODEL,
        "cost_boundary": "Local Ollama/Qwen only. No paid API and no Zep graph build.",
    }
    for item in analyses:
        aggregate_stats["relevance_counts"][item["relevance"]] = aggregate_stats["relevance_counts"].get(item["relevance"], 0) + 1

    mod.write_csv(out_dir / f"document_evidence_table{a.suffix}.csv", analyses)
    (out_dir / f"document_evidence{a.suffix}.json").write_text(json.dumps(analyses, ensure_ascii=False, indent=2), encoding="utf-8")
    # ---- end of replay ----

    # preflight annotations (added keys only; original keys above are unchanged)
    aggregate_stats["preflight_stage"] = "stage1_rule_counting_only"
    aggregate_stats["qwen_inference_executed"] = False
    aggregate_stats["note"] = "The 'model' key repeats the constant in the analysis script; no Ollama request was made in this run."
    (out_dir / f"manifest{a.suffix}.json").write_text(json.dumps(aggregate_stats, ensure_ascii=False, indent=2), encoding="utf-8")

    run_info = {
        "started": started,
        "finished": dt.datetime.now().isoformat(timespec="seconds"),
        "python": sys.version,
        "platform": platform.platform(),
        "hostname": socket.gethostname(),
        "analysis_script": str(script),
        "analysis_script_sha256": sha256_file(script),
        "input_file": str(input_file),
        "input_sha256": sha256_file(input_file),
        "documents_parsed": len(documents),
        "outputs": {
            "csv": str(out_dir / f"document_evidence_table{a.suffix}.csv"),
            "json": str(out_dir / f"document_evidence{a.suffix}.json"),
            "manifest": str(out_dir / f"manifest{a.suffix}.json"),
        },
        "qwen_inference_executed": False,
    }
    (out_dir / f"run_info{a.suffix}.json").write_text(json.dumps(run_info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"documents_parsed": len(documents), "category_totals": aggregate_stats["category_totals"],
                      "relevance_counts": aggregate_stats["relevance_counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
