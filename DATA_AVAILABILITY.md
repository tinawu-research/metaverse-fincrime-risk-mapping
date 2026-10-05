# Data Availability

**Status.** This describes the public reproduction material for a manuscript that is being revised; citation information is to be updated and no licence has been selected.

Full-text PDFs are not redistributed in this package because they may be subject to publisher copyright and licensing restrictions.

This repository covers two analyses with different corpora. See `docs/VERSIONS.md`.

## Obtaining the corpora

**Revised analysis, 65 documents (2026-09).** `lda_65docs_2026-09/tables/corpus_manifest.csv` lists all 65 documents with filename, SHA-256, page count and extraction statistics (983 pages in total; all 65 recorded as computationally included). Users with lawful access can obtain the PDFs, preserve the recorded filenames, and verify each file against the recorded hash before rerunning. Extraction is hash-sensitive: one book chapter is handled by a content-hash-specific page rule, and an edited or re-typeset copy of any file can change the results.

**Original analysis, 59 documents (2026-06).** The canonical input folder was documented as `Submission/kumar_MV`. It is not included here. A per-file hash manifest equivalent to the one above was not produced for this corpus.

The two corpora overlap in 58 documents.

## What this package provides

For both analyses:

- analysis code;
- run metadata and provenance notes;
- aggregate topic-model outputs;
- figures that do not require redistribution of full-text source documents.

For the original analysis additionally:

- redacted Qwen evidence summaries;
- graph edge and provenance tables and redacted graph data.

For the revised analysis additionally:

- the complete pipeline implementation and a reproduction notebook;
- a fully pinned dependency snapshot and the recorded execution environment;
- the run configuration and the model-selection decision record;
- a source-provenance record reconciling the deposited script against the executed script by hash;
- corpus, preprocessing, model-selection, convergence, stability, sensitivity and topic tables;
- same-seed paired sensitivity tables.

## What is intentionally excluded

From the original analysis:

- publisher full-text PDFs;
- duplicate PDF corpus folders;
- full extracted corpus text;
- Qwen batch and report files containing long verbatim excerpts;
- original graph files that embed long document snippets;
- the LDA workbook, which contains extracted-text and long-chunk sheets.

From the revised analysis:

- publisher full-text PDFs;
- the per-document extracted text (raw and cleaned pages, 65 JSON files);
- the 208 fitted model caches, the final fitted model, the dictionary and phrase models, and the unit term-count matrix;
- the run console log;
- the human-review working directory produced by the pipeline.

These exclusions mean the revised analysis can be audited from its recorded tables and rerun from lawfully obtained PDFs, but its saved model objects cannot be reloaded from this repository.

## Quotations from source publications

<!-- DRAFT NOTE, remove before release: this section is written for the case where the
     short-quotation table IS included. It is currently held back pending the author
     team's decision. If the table is not released, delete this section. -->

`lda_65docs_2026-09/tables/appendix_b_verified_short_quotations.csv` contains eleven short verbatim quotations, one per topic, of four to sixteen words each, with the physical PDF page and the source file hash for each. They are reproduced for verification of the topic evidence records. Normalisation applied to the quoted strings is limited to Unicode NFKC and whitespace.

## Human review records

The eleven topic labels of the revised analysis were reviewed by two reviewers who recorded separate decisions, proposed labels and confidence scores, followed by label adjudication (consolidated record dated 2026-09-18; workbooks last modified 2026-09-22). The independence of the pre-discussion ratings rests on the authors' attestation recorded in the workbooks. No inter-rater coefficient was calculated, and the record does not include a page-by-page source check. This is a label review only; it is neither a validation of the topic model nor the topic-threat review. Historical "pending" wording in some supplement files (`model_selection_decision.json`, `tables/human_validation_status.json`, `tables/appendix_b_evidence_records.csv`) is a run-time record and does not describe the current label-review status; see `lda_65docs_2026-09/CURRENT_REVIEW_STATUS.md` and `lda_65docs_2026-09/topic_label_review_anonymised.csv`. `gates_passed: false` for K = 11 is unchanged.

The coder workbooks name the reviewers and are kept internally; an anonymised transcription (Reviewer A/B) is deposited in `lda_65docs_2026-09/`. See `lda_65docs_2026-09/README.md`.

## Qwen and graph evidence layer

The Qwen evidence summaries and graph tables in the repository root correspond to the earlier 59-document corpus. The 65-document Qwen workflow, keyword-count table without excerpts, graph exports without document excerpts and author-decision tables are in `qwen_graph_65docs_2026-10/`. Source PDFs, extracted text, rule-selected excerpts, prompts with excerpts and raw model records that embed excerpts are not deposited; the 65 PDFs must be obtained through the readers' own lawful access route and checked against the SHA-256 values in the corpus manifest. Without them the document-level steps (extraction, keyword counting, Qwen batches, graph rebuild) cannot be re-executed from the deposited material; the deposited exports, decision tables and validation records can be inspected and re-validated.

## Rerunning

Users with lawful access to the source PDFs may rerun extraction and modelling using the code and the notes in `REPRODUCING.md`. Corpus access and copyright conditions are separate from access to the code and the derived records.
