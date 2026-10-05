#!/usr/bin/env python3
"""Re-run the whole pipeline into an empty directory and compare outputs byte-for-byte.

Usage: 05_rerun_check.py --root <graph_65docs_k11_*>
Creates <root>/validation/rerun_clean/ (removed first if present), copies only code/ into it,
runs steps 01, 02, 04, 03 there, then compares sha256 of every file in decisions/,
graph_pack/ and figures/ with the main outputs. Writes validation/rerun_comparison.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import os
from pathlib import Path

sys.dont_write_bytecode = True


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    args = ap.parse_args()
    root = Path(args.root).resolve()
    clean = root / "validation" / "rerun_clean"
    if clean.exists():
        shutil.rmtree(clean)
    clean.mkdir(parents=True)
    shutil.copytree(root / "code", clean / "code", ignore=shutil.ignore_patterns("__pycache__"))
    py = sys.executable
    env = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "MPLCONFIGDIR": str(clean / ".mpl"),
           **{k: v for k, v in os.environ.items() if k.startswith("CHBR_")}}  # pass path variables on
    steps = [
        [py, "code/01_build_decision_records.py", "--out", "."],
        [py, "code/02_build_graph_k11_65docs.py", "--decisions", "decisions", "--out", "graph_pack"],
        [py, "code/04_make_paper_figures.py", "--graph", "graph_pack/graph_data.json", "--out", "figures"],
        [py, "code/03_validate_graph.py", "--root", "."],
    ]
    for cmd in steps:
        r = subprocess.run(cmd, cwd=clean, env=env, capture_output=True, text=True)
        if r.returncode != 0:
            print("STEP FAILED:", cmd, r.stdout[-2000:], r.stderr[-2000:])
            return 1
    rows, ok = [], True
    for sub in ("decisions", "graph_pack", "figures"):
        names = sorted(p.name for p in (root / sub).iterdir() if p.is_file())
        names_clean = sorted(p.name for p in (clean / sub).iterdir() if p.is_file())
        if names != names_clean:
            ok = False
            rows.append({"file": sub, "same": False, "note": f"file lists differ: {set(names) ^ set(names_clean)}"})
        for n in names:
            if n in names_clean:
                a, b = sha(root / sub / n), sha(clean / sub / n)
                same = a == b
                ok &= same
                rows.append({"file": f"{sub}/{n}", "same": same, "sha256_main": a, "sha256_rerun": b})
    # Validation report content (not file, which differs only in absolute root path inside none)
    rep_main = json.loads((root / "validation/validation_report.json").read_text(encoding="utf-8")) if (root / "validation/validation_report.json").exists() else None
    rep_clean = json.loads((clean / "validation/validation_report.json").read_text(encoding="utf-8"))
    same_val = rep_main is not None and rep_main == rep_clean
    out = {"all_files_byte_identical": ok, "n_files_compared": len(rows),
           "validation_report_identical": same_val, "rerun_validation_all_pass": rep_clean["all_pass"],
           "rerun_summary": rep_clean["summary"], "files": rows}
    (root / "validation" / "rerun_comparison.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"compared {len(rows)} files; byte-identical={ok}; validation report identical={same_val}; rerun validation pass={rep_clean['all_pass']}")
    return 0 if ok and rep_clean["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
