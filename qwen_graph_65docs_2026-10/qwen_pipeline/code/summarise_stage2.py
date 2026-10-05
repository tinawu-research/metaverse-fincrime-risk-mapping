#!/usr/bin/env python3
"""summarise_stage2.py -- post-run summary of Stage 2 from the recorded artefacts only (no model call).
Reports: batch coverage (65 doc_ids exactly once), per-batch completion (done_reason), prompt/eval token counts,
wall time, whether each batch summary mentions each of its 5 DOC_IDs, final synthesis completion + section headings,
identity check verdict and Ollama/GPU facts. Writes stage2_summary.json next to the outputs."""
import json
import re
import sys
from collections import Counter
from pathlib import Path

Q = Path(sys.argv[1])
LOGDIR = Path(sys.argv[2])
JOB = sys.argv[3]

plan = json.loads((Q / "batch_plan.json").read_text(encoding="utf-8"))
ids = plan["document_order"]
status = json.loads((Q / "status.json").read_text(encoding="utf-8")) if (Q / "status.json").exists() else {}
rr = json.loads((Q / "run_record.json").read_text(encoding="utf-8")) if (Q / "run_record.json").exists() else None
idc_path = LOGDIR / ("model_identity_check_%s.json" % JOB)
idc = json.loads(idc_path.read_text(encoding="utf-8")) if idc_path.exists() else {}

rows = []
covered = []
for b in plan["batches"]:
    n = b["batch"]
    rp = Q / "responses" / ("qwen_batch_%02d_response.json" % n)
    md = Q / ("qwen_batch_%02d.md" % n)
    row = {"batch": n, "doc_ids": b["doc_ids"], "response_file": rp.exists(), "md_file": md.exists() and md.stat().st_size > 0}
    if rp.exists():
        r = json.loads(rp.read_text(encoding="utf-8"))
        raw = r["raw_response"]
        text = raw.get("response", "")
        row.update({"complete": r.get("complete"), "done_reason": raw.get("done_reason"),
                    "prompt_eval_count": raw.get("prompt_eval_count"), "eval_count": raw.get("eval_count"),
                    "attempts": len(r.get("attempts", [])), "wall_s": r["attempts"][-1]["wall_seconds"] if r.get("attempts") else None,
                    "total_duration_s": round((raw.get("total_duration") or 0) / 1e9, 1),
                    "words": len(text.split()),
                    "doc_ids_mentioned": sum(1 for d in b["doc_ids"] if d in text),
                    "foreign_doc_ids_mentioned": sorted(set(re.findall(r"\bD[0-9a-f]{12}\b", text)) - set(b["doc_ids"])),
                    "headings_found": len(re.findall(r"(?m)^\s*(?:#+\s*)?\d\.\s", text))})
        if r.get("complete"):
            covered.extend(b["doc_ids"])
    rows.append(row)

final = {}
fp = Q / "responses" / "final_synthesis_response.json"
if fp.exists():
    r = json.loads(fp.read_text(encoding="utf-8"))
    raw = r["raw_response"]
    text = raw.get("response", "")
    sections = ["Executive answer", "Mechanism model", "Financial crime typology matrix", "Modelling and analytical framework",
                "Intervention points", "Indicators and red flags", "Implications", "Research gaps and limitations", "Conclusion"]
    final = {"complete": r.get("complete"), "done_reason": raw.get("done_reason"), "prompt_eval_count": raw.get("prompt_eval_count"),
             "eval_count": raw.get("eval_count"), "wall_s": r["attempts"][-1]["wall_seconds"], "words": len(text.split()),
             "sections_present": {s: (s.lower() in text.lower()) for s in sections},
             "doc_ids_cited": len(set(re.findall(r"\bD[0-9a-f]{12}\b", text))),
             "fit_check": r.get("fit_check")}

summary = {
    "job_id": JOB,
    "status": status,
    "identity_check_verdict": idc.get("verdict"), "ollama_version": idc.get("ollama_version"),
    "identity_results": idc.get("results"),
    "batches_planned": plan["batch_count"],
    "batches_complete": sum(1 for r in rows if r.get("complete")),
    "coverage_65_exactly_once": sorted(covered) == sorted(ids) and len(covered) == 65,
    "done_reasons": dict(Counter(r.get("done_reason") for r in rows)),
    "batches": rows,
    "final_synthesis": final,
    "run_record_present": rr is not None,
    "gpu": (rr or {}).get("ollama_ps_after_run"),
    "tokenizer_calibration": (rr or {}).get("tokenizer_calibration"),
}
(Q / "stage2_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print("identity:", summary["identity_check_verdict"], "| ollama", summary["ollama_version"], "| status:", status.get("stage"))
print("batches complete: %d/%d | coverage exactly once: %s | done_reasons: %s" % (
    summary["batches_complete"], plan["batch_count"], summary["coverage_65_exactly_once"], summary["done_reasons"]))
print("batch | complete | reason | prompt_tok | eval_tok | wall_s | words | own_ids_mentioned/5 | foreign_ids")
for r in rows:
    print("%5d | %s | %s | %s | %s | %s | %s | %s/5 | %s" % (r["batch"], r.get("complete"), r.get("done_reason"),
          r.get("prompt_eval_count"), r.get("eval_count"), r.get("wall_s"), r.get("words"), r.get("doc_ids_mentioned"),
          r.get("foreign_doc_ids_mentioned")))
print("final:", json.dumps(final, ensure_ascii=False)[:600])
