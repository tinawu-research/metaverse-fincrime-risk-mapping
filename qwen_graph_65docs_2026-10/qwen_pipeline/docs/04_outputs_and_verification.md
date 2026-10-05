> **Delivery copy (2026-10-05).** Sanitised from the 2026-09-29 draft: scheduler/account/host identifiers, personal machine details and author names (replaced by reviewer codes) removed; no other change. References to project-relative paths (`qwen_65docs/...`, `internal_reviewer_snapshot_20260929/...`) name files of the project working directory, not files of this delivery; the delivered counterparts are listed in the attachment manifest.

# Outputs and Verification Record — Index

**Status: draft for author review.** This is an organized index over
existing, untouched files, grouped by evidentiary status. Nothing listed
here has been edited, renamed, or moved as part of preparing this package;
every path is where the file already lives. Follow the distinctions in the
section headers carefully — conflating "original Qwen output" with "edited
draft," or "author-reported check" with "this review's own verification,"
is exactly the kind of overclaim this package must not repeat.

**Revised 2026-09-29: self-contained copies added.** The paths below
(under `qwen_65docs/review/` and `qwen_65docs/qwen/`) are server-only —
useful for internal working reference, but not reachable by a reviewer or a
journal's supplementary-materials system. Actual, sha256-verified copies of
every file in §§1–5 below are now also in
`internal_reviewer_snapshot_20260929/` (`outputs/` for §1,
`verification/` for §§2–5) — see that folder's own `00_SNAPSHOT_README.md`.
Use the snapshot copies for anything leaving this server; use the paths
below only for locating the maintained, current version during further
internal work.

## 1. Original Qwen outputs (model-generated text, unedited)

| File | What it is |
|---|---|
| `qwen_65docs/qwen/qwen_batch_01.md` … `qwen_batch_13.md` | The 13 batch-level outputs, one per batch, model text exactly as returned by Ollama |
| `qwen_65docs/qwen/qwen_batch_summaries.md` | Concatenation of the 13 batch outputs above (mechanical concatenation, not itself a new generation) — this is what the final-synthesis call actually received as its `{batch_summaries}` input |
| `qwen_65docs/qwen/final_synthesis.md` | The single final-synthesis output, model text exactly as returned by Ollama |
| `qwen_65docs/qwen/complete_analysis_report.md` | A **programmatically assembled report** (by `qwen_65docs/qwen/scripts/summarise_stage2.py`) combining the final synthesis with the 13 batch outputs into one document for readability — **not itself an additional model generation**; do not describe it as a ninth Qwen call |

All of the above are byte-for-byte as Ollama returned them or as a
non-generative script assembled them; none have been edited by any review
round. `final_synthesis.md` contains **zero DOC_ID citations** in its
original form, confirmed by direct inspection.

## 2. Editorial revision (a proposal, not an approved text, not a Qwen output)

`qwen_65docs/review/05_synthesis_editorial_draft.md` is a **human-prepared
editorial rewrite** of `final_synthesis.md` — it is clearly headed as such
in the file itself, it is not a new model generation, and it is not an
author-approved manuscript text. It:

- keeps and cites (author–year in the reader-facing text, DOC_ID in the
  technical crosswalk) the claims independently traced to a specific
  document-level source;
- drops (not hedges) claims found to have no basis in anything Qwen was
  shown, including one confirmed fabricated conflation;
- replaces a model-generated "Research Gaps" list with a fixed statement
  about the pipeline's own structural limitations.

Every change between `final_synthesis.md` and this draft, with its
evidential basis, is logged in
`qwen_65docs/review/06_editorial_change_log.md` (three rounds: initial
evidence-based trimming, a restructuring pass for evidentiary precision, and
a 2026-09-28 pass implementing Reviewer A's nine corrections — see §4 below).

**Authors should review `05_synthesis_editorial_draft.md` against its cited
source evidence before deciding what, if anything, to carry into the
manuscript.** This review can happen independently of the separate,
unresolved Stage ③ (topic→threat mapping) track.

## 3. Traceability table (targeted claim-traceability and source checks)

`qwen_65docs/review/02_synthesis_traceability.md` — for every claim that was
a candidate for retention or removal in the editorial draft, states which of
two evidence levels applies:

- **"Supported in batch output"**: a specific document-level bullet in one
  of the 13 batch outputs names the claim (one model generation, not
  independently checked further).
- **"Verified against extracted source text"**: additionally located and
  confirmed against the matching passage in
  `qwen_65docs/preflight/all_extracted_text_65docs.txt` (the full
  rule-extracted corpus text the excerpts were drawn from). Source PDF pages
  themselves were not opened for this table's own checks (see §4 for the
  subset that also has physical-PDF-page verification).

It also documents 5 claims found **unsupported by all three synthesis
inputs** (removed from the editorial draft) and one **confirmed fabricated
conflation** (the NFT-energy-consumption/transaction-concealment claim).

## 4. Reviewer A's spot-check: author-reported check + this review's independent verification

**Keep these two things separate, as the source files do.** Reviewer A reported
(via the user) completing an AI-assisted check of the original PDF passages
behind nine specific claims in the editorial draft, citing physical PDF
pages for each — this is recorded as **his own reported check**, not as
prior independent verification by this review.

Separately, `qwen_65docs/review/handoff_20260928/01_reviewer_A_spot_check_record.md`
records what **this review independently did**: for each of his nine items,
identified the DOC_ID, located the actual PDF, extracted the exact physical
page with `pdftotext -f N -l N`, read it directly, and confirmed (or in one
sub-case, refined) whether the passage supports the wording now used.
Full bibliographic detail (author list, venue, DOI, physical page, which
wording each page supports) for all 12 sources involved is in
`qwen_65docs/review/handoff_20260928/02_citation_crosswalk.md` /
`.csv`, and complete, paste-ready APA references (with two author-list
corrections and three resolved book editors found on a full-PDF re-read) are
in `qwen_65docs/review/handoff_20260928/07_followup_apa_and_status.md` §1.

**Explicitly, per instruction: none of this — Reviewer A's check or this
review's independent verification — should be characterised as a blind
review, a random sample, independent double-coding, an overall error-rate
estimate for `final_synthesis.md`, or a full-text human verification of all
65 documents.** It is a targeted, page-specific check of 12 sources cited
for 9 items.

## 5. Change log (every substantive edit, with its basis)

`qwen_65docs/review/06_editorial_change_log.md` — three dated rounds
(Round 1: initial evidence-based trimming/citing; Round 2, 2026-09-22:
restructuring so batch-recurrence is no longer presented as corroborating
evidence; Round 3, 2026-09-28: Reviewer A's nine corrections plus switching
reader-facing citations to author–year). 18 + 13 + 12 = 43 individually
logged changes in total, each tagged Addition / Removal / Correction /
Qualification / Restructure with its evidential basis.

## 6. Supporting checks (keyword counts, corpus identity)

**Not part of what R1.4d/R2.4c ask for** (see
`05_file_index_and_reviewer_responses.md` §3) — kept here only as adjacent
background, with its current, corrected status as of 2026-09-29:

- `qwen_65docs/review/handoff_20260928/03_keyword_counts_and_classification.md`
  (copy also in `internal_reviewer_snapshot_20260929/verification/`) — the
  four category totals (16,886 / 9,990 / 1,542 / 4,890) and the 17/48
  relevance split for the 65-document corpus, cross-checked against three
  independent artefacts, byte-identical across two Python versions. **Do
  not reuse the old 59-document totals** (14,681 / 9,022 / 1,430 / 4,407;
  14/45) — not proportional or convertible. This item is unaffected by the
  correction below.
- **Corpus identity (Calvo exclusion; the "79/14/65" totals): current
  status, correcting this package's own prior wording.** An earlier pass of
  this package described the Calvo (2023) exclusion as having no documented
  reason, and the "79 assessed / 14 excluded / 65 included" figure as
  unreconciled by any record found. **Both statements are now out of date**
  — per
  `qwen_65docs/review/handoff_20260928/08_drive_verification_and_k11_mapping.md`
  §§2–3 (2026-09-28, the current account; supersedes §2/§3 of
  `04_corpus_identity_check.md` and §§2–3 of `07_followup_apa_and_status.md`,
  both of which predate the Drive-verified material and are marked
  superseded-in-part at their own file tops):
  - **Exclusion reasons for Calvo (2023) are recorded in the workbook.** The
    same publication (same DOI) appears as two rows in
    `Processed_Titles_30Oct_del.xlsx!Excluded`: `S231` gives a scope-based
    reason ("does not specifically investigate security threats or
    financial crime mechanisms"); `S392` gives a language-based reason
    ("the paper is in Spanish"). The workbook's own file/row timestamp is
    not the same thing as the date the exclusion decision was made, and
    this package does not claim to know that date — only that a stated
    reason is recorded. What remains open is which reason the authors
    intend as primary, and de-duplicating the count to one exclusion rather
    than two rows — **not** "no reason on record."
  - **"79 assessed / 14 excluded / 65 included" are manuscript-reported
    totals whose composition and screening sequence await author
    confirmation.** The manuscript already reports these totals; this
    package does not treat them as missing or as "unreconciled by any
    record." What is **not yet confirmed** is the composition and screening
    sequence behind them (including a six-vs-seven-additions wording
    question) and their correspondence to the underlying workbook.
  - **Both open points have already been sent to Reviewer B/Reviewer A by the user,
    and a reply is pending** — this package does not re-raise them as new
    questions or suggest contacting the authors again.
  - The 7 newly added documents' identities (title/author/DOI) from the
    prior round remain correct and unaffected by this correction.
- **Bhaskar et al. citation year:** this round continues to use (2024), as
  already adopted in `07_followup_apa_and_status.md` §1 ref. 1, alongside
  the recorded CrossRef metadata-date difference (2023-11-27) kept on file
  for completeness. Not treated as a blocker to this package.

## 7. What this index does not include

Stage ③ (K=11 topic-label verification, topic→threat mapping) is a separate
track and is intentionally not indexed here — see
`qwen_65docs/review/03_topic_threat_mapping.md` and
`qwen_65docs/review/handoff_20260928/08_drive_verification_and_k11_mapping.md`
/ `09_k11_topic_threat_author_review_table.md` if that track is needed for a
different reviewer item. Nothing in R1.4d/R2.4c requires it.
