# Revised LDA analysis - 65 publications (2026-09)

This directory is self-contained. Its code, pinned dependencies, run configuration and results belong to the revised analysis only, and must not be mixed with the original 2026-06 analysis in the repository root. See `../docs/VERSIONS.md`.

**No new topic models were fitted when preparing this directory.** Everything here is the recorded output of one completed run, plus one helper that reads saved models without fitting.

## Status

**Status.** Revised 65-document topic-model material for a manuscript that is being revised. K = 11 is an exploratory working model that did not pass the declared stability threshold (see below).

**Analytical choice.** The author team has selected **K = 11, medoid seed 2026, as the exploratory working model**, with **K = 8 retained as a more parsimonious comparison**. The results here are reported on that basis. This is a settled choice; it is not pending.

**Stability qualification, which is a separate matter.** No coherence-shortlisted candidate passed the declared seed-stability threshold, and `model_selection_decision.json` records `gates_passed: false`. The automatic rule returned K = 11 as a fallback after that gate failed, not as a validated optimum. Full-corpus matched seed similarity at K = 11 is about 0.39 against a declared threshold of 0.70.

**Therefore: do not describe K = 11 as stable, validated, or an established optimal topic count, and do not present the eleven topics as a confirmed structure.** Selecting it as the working model does not discharge this qualification, which travels with every result reported from this directory.

Further status:

- `verification.json` reports internal consistency checks only. Its own scope statement applies: software consistency, not substantive topic validity.
- The eleven topics carry keyword-derived labels. The eleven topic labels of the revised analysis were reviewed by two reviewers who recorded separate decisions, proposed labels and confidence scores, followed by label adjudication (consolidated record dated 2026-09-18; workbooks last modified 2026-09-22). The independence of the pre-discussion ratings rests on the authors' attestation recorded in the workbooks. No inter-rater coefficient was calculated, and the record does not include a page-by-page source check. This is a label review only; it is neither a validation of the topic model nor the topic-threat review. Historical "pending" wording in some supplement files (`model_selection_decision.json`, `tables/human_validation_status.json`, `tables/appendix_b_evidence_records.csv`) is a run-time record and does not describe the current label-review status; see `lda_65docs_2026-09/CURRENT_REVIEW_STATUS.md` and `lda_65docs_2026-09/topic_label_review_anonymised.csv`. `gates_passed: false` for K = 11 is unchanged.
- Publication-type sensitivity is not run: it requires verified study-type metadata, and study type is still `unknown` in `tables/metadata_template.csv` (year and screening ID are filled from the study-selection record) and no quality appraisal exists; see `METADATA_SOURCES_AND_GAPS.md`.
- This directory covers the **topic model only**. The Qwen/Ollama workflow and the K = 11 graph for this corpus are in `qwen_graph_65docs_2026-10/`.

## Contents

| Path | Contents |
|---|---|
| `Metaverse_LDA_Colab.py` | Complete pipeline, version 1.0.1 |
| `Run_LDA.ipynb` | Reproduction notebook with the script, requirements and configuration embedded. Deposited unexecuted: no saved execution counts, no saved outputs |
| `audit_paired_sensitivity.py` | Same-seed comparison of saved baseline and alternative K=11 fits. Loads saved models; fits nothing |
| `run_config.json` | Recorded research configuration. Input and output paths are supplied at execution |
| `requirements-resolved.txt` | Complete pinned package snapshot of the recorded run |
| `environment_versions.json` | Recorded execution environment, including the executed source hash |
| `source_provenance.json` | Executed and deposited source hashes, and the two preparation changes |
| `model_selection_decision.json` | Recorded selection rule, outcome and qualifications |
| `verification.json` | Internal consistency checks |
| `tables/` | Corpus manifest and hashes, preprocessing records, model-selection and convergence diagnostics, stability and sensitivity tables, topic and evidence records |
| `tables/legacy_reference_seed/` | The earlier sensitivity comparison against the representative model, retained for provenance. Different comparison base; not interchangeable with the paired tables |
| `figures/` | Nine figure families in PNG, SVG and PDF |
| `lda_interactive.html` | pyLDAvis display for this model. Circle areas are token-weighted, not the equal-publication prevalence reported in the manuscript |
| `keyword_cooccurrence.graphml.xml` | Keyword co-occurrence network. Descriptive only; not independent confirmation of the topic model |

## Deposited source vs executed source

`Metaverse_LDA_Colab.py` as deposited is not byte-identical to the script that produced these results, and the two hashes are recorded in `source_provenance.json` and `environment_versions.json`:

- executed: `67cdd428d650cb9781cc98875a8476b7efc76bb86b0d5fe33bd354b706034e5b`
- deposited: `0e42f078db4650d92eef9c92bb5df69f23e4e0c51f4fb66c4bd330af641252fc`

The two differences are the module description and one document-link constant, which was changed from a private working-document URL to the local crosswalk filename. Neither is on any computation path. `Run_LDA.ipynb` embeds the deposited version, byte-for-byte.

## Running

See `../REPRODUCING.md`, Part 1. In short: install `requirements-resolved.txt` into its own environment, obtain the 65 PDFs, verify them against `tables/corpus_manifest.csv`, then run the research profile. It performs 208 fits and is a substantial computation.

## Reading the sensitivity tables

Use `tables/paired_sensitivity_summary.csv` and `paired_sensitivity_pairs.csv`. Each variant is compared against the **same-seed** saved K=11 baseline, which separates the specification effect from seed-to-seed variation.

Read alongside the recorded seed instability: the full-corpus K=11 matched seed similarity is about 0.39. Comparisons made against a single representative model, as in `tables/legacy_reference_seed/`, sit at a similar level for every variant and therefore cannot distinguish a specification effect from seed variation. The paired tables are the ones to cite.

One result to read carefully: `uncapped_training_chunks` shows a similarity of exactly 1.0 and a maximum absolute difference of 0.0. The configured cap of 50 training chunks per document never binds, because the largest document yields 35 units (`tables/document_chunk_counts.csv`). The variant is a no-op control, not evidence of robustness.

`paired_sensitivity_pairs.csv` carries a `basis` column documenting the comparison base per row. That column was added when the appendix tables were assembled and is not emitted by `audit_paired_sensitivity.py`; the summary table matches the script's columns exactly.

## Figure to appendix mapping

<!-- DRAFT NOTE, remove before release: the supplement text refers to figures as
     S1-S4 but no mapping to filenames exists in the delivered material. Fill this
     table from the manuscript appendices before release; do not guess. -->

| Appendix figure | File | Status |
|---|---|---|
| S1 convergence | `figures/final_convergence_trace.*` | to be confirmed against the appendix |
| S2 unit counts | `figures/chunk_count_distribution.*` | to be confirmed against the appendix |
| S3 prevalence | `figures/average_topic_prevalence.*` | to be confirmed against the appendix |
| S4 publication mixtures | not identified | to be confirmed against the appendix |

Other figures in this directory are not referenced by those labels: `model_selection_diagnostics.*`, `document_topic_heatmap.*`, `top10_normalized_keywords.*`, `topic_similarity_cosine.*`, `topic_similarity_js.*`, `keyword_cooccurrence_network.*`.
