#!/usr/bin/env python3
"""Server-side recheck of the three PDFs the authors could not locate on 1 Oct 2026.

For D28078c8a10cc, Dfed6d84a0e4f and Db80703b6ee6c: confirm the server copy's SHA-256 and
page count equal the corpus manifest, and record the text of the cited physical page that
contains the key phrases quoted in the Decision Guide / review table. This is a check that
the *passage exists on the cited page of the manifest-identical file*; it is not an author
re-review and does not assess the study's quality or the interpretation of the passage.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import os
from pathlib import Path

sys.dont_write_bytecode = True

SYNC = Path(os.environ["CHBR_PROJECT_ROOT"])
PDF_DIR = SYNC / "CHBR_LDA_comparison_20260915/antigravity/input_pdfs"
MANIFEST = SYNC / "CHBR_revision_sync_20260922/incoming/Electronic_Supplement_A1/tables/corpus_manifest.csv"

# doc -> list of (pair(s), physical page, regexes that must all match the page text)
TARGETS = {
    "D28078c8a10cc": [
        ("T05>TH_SCAM; T05>TH_CYBER", 8, [r"significant public distrust", r"fraud and\s+cybercrime", r"audit control"]),
        ("T05>TH_GOVERNANCE", 8, [r"guarantor of the legitimacy", r"compliance with internal regulations", r"legal field"]),
    ],
    "Dfed6d84a0e4f": [
        ("T06>TH_SCAM; T06>TH_NFT", 6, [r"money laundering scheme", r"Ponzi scheme", r"enormous scamming"]),
    ],
    "Db80703b6ee6c": [
        ("T08>TH_SCAM", 2, [r"hacking and transaction fraud", r"phishing and smishing"]),
    ],
}


def page_text(pdf: Path, page: int) -> str:
    r = subprocess.run(["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf), "-"],
                       capture_output=True, text=True, errors="replace")
    return r.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    man = {}
    with MANIFEST.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            man[r["document_id"]] = r
    res, ok = [], True
    for doc, items in TARGETS.items():
        m = man[doc]
        pdf = PDF_DIR / m["filename"]
        h = hashlib.sha256(pdf.read_bytes()).hexdigest()
        info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, errors="replace").stdout
        pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
        rec = {"doc_id": doc, "server_path": str(pdf.relative_to(SYNC)), "sha256_server_copy": h,
               "sha256_manifest": m["sha256"], "sha256_equal": h == m["sha256"],
               "pages_server": pages, "pages_manifest": int(m["page_count"]), "pages_equal": pages == int(m["page_count"]),
               "page_checks": []}
        ok &= rec["sha256_equal"] and rec["pages_equal"]
        for pair, page, pats in items:
            txt = re.sub(r"[ \t]+", " ", page_text(pdf, page))
            flat = re.sub(r"\s+", " ", txt)
            hits = {p: bool(re.search(p, flat, flags=re.I)) for p in pats}
            ok &= all(hits.values())
            rec["page_checks"].append({"pairs": pair, "physical_page": page, "phrases_found": hits,
                                       "all_found": all(hits.values())})
        res.append(rec)
    out = {
        "scope": "Existence of the quoted phrases on the cited physical page of the manifest-identical server copy (pdftotext). Not an author re-review.",
        "all_ok": ok, "documents": res,
    }
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("all_ok =", ok)
    for r in res:
        print(r["doc_id"], "sha256_equal", r["sha256_equal"], "pages_equal", r["pages_equal"],
              [(c["physical_page"], c["all_found"]) for c in r["page_checks"]])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
