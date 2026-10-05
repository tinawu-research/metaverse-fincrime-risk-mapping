# Metaverse-Cryptocurrency Financial Crime Reproducibility Package

This repository is a reproducibility package for the paper provisionally titled **Mapping Financial Crime Risks in the Metaverse-Cryptocurrency Ecosystems: A Topic-Modelling and Local LLM-Assisted Evidence Synthesis**.

It contains code, metadata, provenance notes, selected aggregate outputs, redacted derived tables, and figures for auditing the computational workflow.

**Status.** Public reproduction material for a manuscript that is being revised. Paper citation information (authors, DOI, journal, date) is **to be updated**; no licence has been selected. Cite or rely on it accordingly. Repository: <https://github.com/tinawu-research/metaverse-fincrime-risk-mapping>.

**Where to start.** Original 59-document gensim analysis: `code/`, `outputs/`, `figures/`, `metadata/`, `requirements.txt` (unchanged). Revised 65-document analysis: topic model (scikit-learn) in `lda_65docs_2026-09/`; Qwen workflow and K = 11 graph in `qwen_graph_65docs_2026-10/`. Version map: `docs/VERSIONS.md`. Run instructions: `REPRODUCING.md`.

## Two analysis versions are present in this repository

This repository holds **two distinct topic-modelling analyses**. They are different corpora *and* different implementations. They must not be combined, and their dependency files are not interchangeable.

| | Original analysis (2026-06) | Revised LDA (2026-09) |
|---|---|---|
| Location | `code/`, `outputs/`, `figures/`, `metadata/` | `lda_65docs_2026-09/` |
| Corpus | 59 full-text documents | 65 full-text documents |
| LDA implementation | gensim `LdaMulticore`, single seed 42 | scikit-learn `LatentDirichletAllocation`, five seeds |
| Candidate topic counts | K = 3 to 8 | K = 2 to 12 |
| Retained solution | seven topics | K = 11 working model, K = 8 comparison (see below) |
| Dependencies | `requirements.txt` | `lda_65docs_2026-09/requirements-resolved.txt` |
| Qwen / graph layer | yes, built on this corpus (root `code/`, `outputs/`) | yes, in `qwen_graph_65docs_2026-10/` (K = 11 graph) |

The two corpora overlap in 58 documents. One document is only in the 2026-06 corpus; seven documents are only in the 2026-09 corpus. Topic numbers are **not** comparable across the two versions: the original T1-T7 and the revised T01-T11 have no correspondence and must never be mapped onto each other by number.

See `docs/VERSIONS.md` for the file-level map.

## Status of the revised LDA (2026-09)

The author team has selected **K = 11 as the exploratory working model** for the revised analysis, with **K = 8 retained as a more parsimonious comparison**. That is a settled analytical choice, and the deposited results are reported on that basis.

It is a separate matter that the model did not clear the project's own stability criterion. No coherence-shortlisted candidate passed the declared seed-stability threshold, and `lda_65docs_2026-09/model_selection_decision.json` records `gates_passed: false`; the automatic rule therefore returned K = 11 as a fallback rather than a validated optimum. **K = 11 must not be described as stable, validated, or an established optimal topic count.** Choosing it as the working model does not change that, and the qualification travels with every result reported from it.

The eleven topic labels of the revised analysis were reviewed by two reviewers who recorded separate decisions, proposed labels and confidence scores, followed by label adjudication (consolidated record dated 2026-09-18; workbooks last modified 2026-09-22). The independence of the pre-discussion ratings rests on the authors' attestation recorded in the workbooks. No inter-rater coefficient was calculated, and the record does not include a page-by-page source check. This is a label review only; it is neither a validation of the topic model nor the topic-threat review. Historical "pending" wording in some supplement files (`model_selection_decision.json`, `tables/human_validation_status.json`, `tables/appendix_b_evidence_records.csv`) is a run-time record and does not describe the current label-review status; see `lda_65docs_2026-09/CURRENT_REVIEW_STATUS.md` and `lda_65docs_2026-09/topic_label_review_anonymised.csv`. `gates_passed: false` for K = 11 is unchanged.

## Status of the Qwen and graph layer

The Qwen evidence pass and the graph/intervention framework in `outputs/qwen/`, `outputs/graph/` and `figures/graph/` were built on the **59-document** corpus and a seven-topic model.

**The Qwen evidence pass and the K = 11 topic-threat graph for the final 65-document corpus are in `qwen_graph_65docs_2026-10/`.** They are the evidence layer of the revised manuscript; the 59-document Qwen and graph material in the repository root (`code/`, `outputs/qwen/`, `outputs/graph/`, `figures/graph/`) belongs to the original analysis only and is kept unchanged. In the revised graph (118 nodes, 544 edges) only the 24 topic-threat relations were reviewed by the authors; 447 edges are rule-generated and 73 are fixed conceptual links carried over from the earlier implementation. The model and graph material is an exploratory analysis: the model stage was run once and its output reproduction is not claimed, and no stability analysis of the LLM-assisted synthesis has been carried out. See `qwen_graph_65docs_2026-10/README.md`.

## What This Package Contains

- Original-analysis LDA notebook and local Qwen/Ollama workflow scripts in `code/`.
- Revised 65-document LDA implementation, configuration, environment record, result tables and figures in `lda_65docs_2026-09/`. This directory covers the topic model only.
- Revised 65-document Qwen/Ollama workflow, K = 11 topic-threat graph, author-decision tables and validation records in `qwen_graph_65docs_2026-10/`.
- Run metadata, graph provenance, and workflow manifests in `metadata/`.
- Safe aggregate LDA outputs in `outputs/lda/`.
- Redacted Qwen evidence summaries in `outputs/qwen/`.
- Graph edge tables, provenance tables, redacted graph data, and graph matrices in `outputs/graph/`.
- LDA and graph figures in `figures/`.
- Version map, reproducibility notes, path-handling note, exclusion rationale and a full code listing in `docs/`.

## What This Package Does Not Contain

This package does not redistribute full-text PDFs, full extracted corpus text, or Qwen batch/report files that contain long verbatim excerpts from source publications. Those files are excluded because they may contain copyrighted publisher material.

For the revised analysis it additionally excludes the per-document extracted text, the fitted model caches and the final model object. See `DATA_AVAILABILITY.md`.

Users who want to fully rerun PDF extraction must lawfully obtain the source PDFs themselves. See `REPRODUCING.md`.

## Workflow Overview (original analysis, 2026-06)

The study used a PRISMA-informed corpus construction process to identify a corpus of 59 full-text documents. The corpus was processed in Python and modelled with Latent Dirichlet Allocation. Candidate topic counts from K=3 to K=8 were evaluated with coherence and model diagnostics, and a seven-topic solution was retained.

After topic modelling, a locally hosted Qwen 2.5 model through Ollama was used as an interpretive aid to organise extracted evidence into evidence dimensions, threat environments, analytical signals, and intervention points. The graph/intervention framework was then built locally. Document-to-evidence and document-to-threat graph edges are rule-generated; topic-to-threat and threat-to-intervention mappings are interpretive conceptual mappings for author review. The topic labels and prevalence values used by the graph builder are recorded as literal values inside `code/05_build_free_graph_pack.py`; they are not read from the LDA output files.

## Repository Layout

- `code/` - original-analysis LDA notebook and local Qwen/graph-building scripts (59 documents).
- `outputs/lda/` - CSV exports of original-analysis aggregate topic-model outputs.
- `outputs/qwen/` - redacted document-level evidence counts and aggregate Qwen manifest values (59 documents).
- `outputs/graph/` - graph edge/provenance tables, intervention matrix, and redacted graph JSON (59 documents).
- `metadata/` - original-analysis run metadata, graph provenance, manifests, and model notes.
- `figures/` - original-analysis LDA and graph figures.
- `lda_65docs_2026-09/` - revised 65-document LDA: code, pinned dependencies, run configuration, environment and source provenance records, result tables, figures.
- `qwen_graph_65docs_2026-10/` - revised 65-document Qwen/Ollama workflow and K = 11 topic-threat graph: code, descriptions, anonymised author-decision tables, exports without document excerpts, validation records.
- `docs/` - version map (`VERSIONS.md`), path-handling note, excluded-file list, full code listing of the original analysis.

## Reading limits (revised 65-document material)

* **K = 11** is the authors' exploratory working model (K = 8 the parsimonious comparison). It did **not** pass the declared cross-seed stability threshold (`gates_passed: false`); it is not a validated or stable topic count.
* **Qwen/Ollama.** The model stage was run once (2026-09-22, 13 batches + one final synthesis). A formal random-sample consistency check of the LLM evidence extraction and a repeated-generation stability check were **not carried out**; this is a disclosed methodological limitation. The code copies in `qwen_graph_65docs_2026-10/` did not regenerate any Qwen output: only the deterministic rule stage and the graph steps were re-run to check the code. Reproduction of the model text is not claimed.
* **Graph.** Of 544 edges only 24 topic-threat relations were reviewed by the authors; 447 are rule-generated document relations (keyword matches, not author-reviewed) and 73 are fixed conceptual links carried over from the earlier implementation (not reviewed in this round). Consistency checks of the graph files are not scientific validation.
* Keyword totals are counts of lexicon-term hits, not densities or evidence-quality scores.
* Source PDFs, extracted text and excerpt-bearing model records are not distributed; steps that need them cannot be re-run from this repository alone (`DATA_AVAILABILITY.md`).

## Paths and provenance

The original 59-document scripts in `code/` still contain absolute paths from an author's machine; they are historical run records and were not modified. The revised 65-document code reads its paths from environment variables or command-line arguments (`REPRODUCING.md`, `qwen_graph_65docs_2026-10/README.md`); every difference between a published code copy and the script that was executed is listed in `qwen_graph_65docs_2026-10/CODE_CHANGE_LOG.md` and `SNAPSHOT_LEDGER.csv`, with hashes.

## Citation

Citation information for the paper (authors, DOI, journal, publication date) is **to be updated**. Until then, please refer to this repository by its link: <https://github.com/tinawu-research/metaverse-fincrime-risk-mapping>. (The earlier `CITATION.cff` contained an unverified author name and a placeholder repository URL and was removed.)

## License Status

No open-source license has been selected yet. See `LICENSE_NOTICE.md`.
