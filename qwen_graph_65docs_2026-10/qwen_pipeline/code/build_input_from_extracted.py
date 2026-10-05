#!/usr/bin/env python3
"""
build_input_from_extracted.py  --  Preflight step 7.2 (handover 01_Qwen更新任务交接_20260922.md)

Single responsibility: convert the 65 extracted JSON files (field `raw_pages`) into ONE text file whose
per-document header block is parseable by `parse_documents()` in
metaverse-fincrime-reproducibility-package/code/01_local_qwen_metaverse_fincrime_analysis.py (lines 60-81).

It performs NO rule counting and calls NO analysis logic. It only reformats.

Format written per document (identical to the historical 59-document input `Appendix 4. Extracted Text.txt`):

    ====================================================================================================
    DOC_ID: <document_id>
    FILENAME: <filename>
    PAGES: <page_count>
    EXTRACTED_WORDS: <raw_words>                <- field used: raw_words (recorded in the output manifest)
    ====================================================================================================

    <raw_pages joined with a blank line between pages>

Fail-loud rules (script exits non-zero, writes nothing):
  * a manifest document_id has no <document_id>.json, or a JSON file has no manifest row
  * `raw_pages` missing / not a list of strings
  * len(raw_pages) != manifest page_count
  * whitespace word count of the joined raw_pages != manifest raw_words
  * a body line starts with "DOC_ID:" (would create a phantom document for the parser)
Reads only the extracted directory and the manifest. Writes only --out-txt and --out-manifest.
"""
import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

SEP = "=" * 100
PAGE_JOIN = "\n\n"
WORD_FIELD = "raw_words"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(msg: str):
    sys.stderr.write("BUILD FAILED: " + msg + "\n")
    sys.exit(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extracted-dir", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out-txt", required=True)
    ap.add_argument("--out-manifest", required=True)
    a = ap.parse_args()

    ext_dir = Path(a.extracted_dir)
    man_path = Path(a.manifest)
    if not ext_dir.is_dir():
        fail(f"extracted dir not found: {ext_dir}")
    if not man_path.is_file():
        fail(f"manifest not found: {man_path}")

    with man_path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    needed = {"document_id", "filename", "page_count", "raw_words", "cleaned_words", "sha256", "status"}
    missing_cols = needed - set(rows[0].keys())
    if missing_cols:
        fail(f"manifest lacks columns: {sorted(missing_cols)}")

    ids = [r["document_id"] for r in rows]
    if len(ids) != len(set(ids)):
        fail("duplicate document_id values in manifest")

    json_files = sorted(ext_dir.glob("*.json"))
    json_ids = {p.stem for p in json_files}
    missing_json = [i for i in ids if i not in json_ids]
    extra_json = sorted(json_ids - set(ids))
    if missing_json or extra_json:
        fail(f"manifest/JSON mismatch. manifest ids without JSON: {missing_json}; JSON without manifest row: {extra_json}")

    blocks = []
    out_rows = []
    total_pages = 0
    total_words = 0
    for r in rows:  # manifest row order is preserved
        did = r["document_id"]
        jp = ext_dir / f"{did}.json"
        with jp.open(encoding="utf-8") as f:
            d = json.load(f)
        pages = d.get("raw_pages")
        if not isinstance(pages, list) or not all(isinstance(p, str) for p in pages):
            fail(f"{did}: raw_pages missing or not a list of strings")
        if len(pages) != int(r["page_count"]):
            fail(f"{did}: len(raw_pages)={len(pages)} != manifest page_count={r['page_count']}")
        body = PAGE_JOIN.join(pages).strip()
        wc = len(body.split())
        if wc != int(r[WORD_FIELD]):
            fail(f"{did}: joined raw_pages word count {wc} != manifest {WORD_FIELD}={r[WORD_FIELD]}")
        if re.search(r"(?m)^DOC_ID:", body):
            fail(f"{did}: body contains a line starting with 'DOC_ID:' (parser hazard)")
        header = (
            f"{SEP}\n"
            f"DOC_ID: {did}\n"
            f"FILENAME: {r['filename']}\n"
            f"PAGES: {r['page_count']}\n"
            f"EXTRACTED_WORDS: {r[WORD_FIELD]}\n"
            f"{SEP}\n\n"
        )
        blocks.append(header + body + "\n\n")
        total_pages += len(pages)
        total_words += wc
        out_rows.append({
            "document_id": did,
            "filename": r["filename"],
            "pages": len(pages),
            "n_empty_raw_pages": sum(1 for p in pages if not p.strip()),
            "word_count_field_used": WORD_FIELD,
            "extracted_words": r[WORD_FIELD],
            "computed_word_count": wc,
            "cleaned_words_manifest": r["cleaned_words"],
            "manifest_status": r["status"],
            "pdf_sha256_from_manifest": r["sha256"],
            "source_json": str(jp),
            "sha256_of_source_json": sha256_file(jp),
        })

    out_txt = Path(a.out_txt)
    out_man = Path(a.out_manifest)
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    with out_txt.open("w", encoding="utf-8", newline="\n") as f:
        f.write("".join(blocks))
    with out_man.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    summary = {
        "documents_written": len(blocks),
        "pages_total": total_pages,
        "words_total": total_words,
        "word_count_field_used": WORD_FIELD,
        "page_join": repr(PAGE_JOIN),
        "out_txt": str(out_txt),
        "out_txt_sha256": sha256_file(out_txt),
        "out_txt_bytes": out_txt.stat().st_size,
        "out_manifest": str(out_man),
        "manifest_sha256": sha256_file(man_path),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
