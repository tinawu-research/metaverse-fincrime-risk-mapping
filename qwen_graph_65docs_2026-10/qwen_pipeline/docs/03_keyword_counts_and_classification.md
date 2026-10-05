> **Delivery copy (2026-10-05).** Sanitised from the 2026-09-29 draft: scheduler/account/host identifiers, personal machine details and author names (replaced by reviewer codes) removed; no other change. References to project-relative paths (`qwen_65docs/...`, `internal_reviewer_snapshot_20260929/...`) name files of the project working directory, not files of this delivery; the delivered counterparts are listed in the attachment manifest.

# Task C — 65-Document Keyword Category Totals and 17/48 Classification

**No text was re-extracted and no Qwen call was made for this task.** All
numbers below are read directly from files already produced by the Stage ①
rule-based pipeline on 2026-09-22 (`qwen_65docs/preflight/`), cross-checked
for internal consistency across three independent artefacts.

## The four category totals (65-document corpus)

| Category | Total keyword-hit count |
|---|---:|
| `metaverse_platform_features` | **16,886** |
| `crypto_ecosystem_features` | **9,990** |
| `financial_crime_opportunities` | **1,542** |
| `modelling_analysis_intervention` | **4,890** |

**Source and field:** `qwen_65docs/preflight/manifest_65.json` →
`category_totals` object. Cross-checked against:
- `qwen_65docs/preflight/preflight_report.md`, §5 (check C9) and the
  aggregate line at the end of §5: "新 65 篇聚合四类计数：16,886 / 9,990 /
  1,542 / 4,890" — identical.
- `qwen_65docs/qwen/requests/final_synthesis_request.json`'s embedded
  aggregate-stats block, per `01_input_content_audit.md` §2.1 (same
  `category_totals` object is what the final Qwen synthesis call actually
  received) — not re-opened byte-for-byte in this round, but this is the
  same `manifest_65.json`-derived object per the Stage ② driver code
  (`run_stage2_qwen.py`), already audited in `01_input_content_audit.md`.
- Independently summable from the per-document rows in
  `document_evidence_table_65.csv` (65 rows) — not re-summed in this round
  since `preflight_report.md` §5/§7.2 already records this file's sha256 as
  identical across two independent Python versions (3.6.15 and 3.12.0),
  which is a stronger consistency check than a manual re-sum would add.

**Do not reuse the old 59-document totals** (14,681 / 9,022 / 1,430 / 4,407 —
recorded in the same `preflight_report.md` §5 as the baseline-recomputation
result, not as a current-corpus number). The two sets are not proportional
or otherwise convertible into each other — the 65-document totals are a
fresh count over re-extracted text (see `04_corpus_identity_check.md` and
`preflight_report.md` §6 for why the same 58 shared documents do not even
produce byte-identical per-document counts across the two extractions).

## The 17/48 relevance classification

| Relevance tier | Count |
|---|---:|
| "primary financial-crime/crypto evidence" | **17** |
| "highly relevant platform/security evidence" | **48** |
| "supporting contextual evidence" | 0 |
| "peripheral or background evidence" | 0 |
| **Total** | **65** |

**Source and field:** `qwen_65docs/preflight/manifest_65.json` →
`relevance_counts` object. Cross-checked against:
- `preflight_report.md` §0 (check C9: "17 + 48 + 0 + 0 = 65 | 通过") and §5.
- `document_evidence_65.json` / `document_evidence_table_65.csv` `relevance`
  field, tallied per-document (17 + 48 = 65, no third or fourth tier
  actually populated despite the schema allowing for them).
- `preflight_report.md` §6.1 also records the internal composition: "新 17
  篇 primary = 旧 14 篇（全部保留档位）+ 新增 3 篇" (the 17 primary documents
  = the 14 old primary documents, all of which kept that tier after
  re-extraction, plus 3 of the 7 newly added documents:
  `Db80703b6ee6c`, `D74bc17aea3dd`, `D9894a8b2bb51` — confirmed against
  `added_7_docs.csv`, which lists these three with `relevance = "primary
  financial-crime/crypto evidence"` and the other four new documents as
  "highly relevant platform/security evidence").

**Do not reuse or rescale the old 59-document 14/45 split** (also recorded
in `preflight_report.md` §5/§6.1 as the historical baseline, reproduced
exactly by this round's Python re-run of the original 2026-05 rule logic on
the *old* input file — not a current-corpus number).

## What Qwen actually received of these numbers (for methods-wording accuracy)

Per `01_input_content_audit.md` §2, the final-synthesis Qwen call received
the aggregate `category_totals` and `relevance_counts` objects above as
**corpus-level sums only** (plus `document_count: 65`, `input_size_bytes`,
`total_extracted_words_reported: 650,617`) — not the per-document counts,
and not the underlying text. The 13 batch calls received only their own
5 documents' individual counts (`category_totals`, `top_terms`), never the
corpus-wide aggregate. This is unchanged from what was already documented;
restated here only to confirm the same two files (`manifest_65.json`'s
numbers) are what both the manuscript-facing totals above and the actual
Qwen input trace back to — there is one source of truth for these four
numbers, not two.

## Consistency verdict

All three independent sources (`manifest_65.json`, `preflight_report.md`,
and the per-document CSV/JSON pair, the latter two also verified
byte-identical across two Python versions on 2026-09-22) agree exactly on
both the four category totals and the 17/48 split. **No discrepancy found.**
