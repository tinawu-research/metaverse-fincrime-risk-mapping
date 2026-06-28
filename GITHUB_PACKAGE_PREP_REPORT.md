# GitHub Package Preparation Report

Date: 2026-06-28

Package folder:

`metaverse-fincrime-reproducibility-package/`

## A. Folder Structure Created

Created a clean candidate repository structure:

- `README.md`
- `REPRODUCING.md`
- `DATA_AVAILABILITY.md`
- `LICENSE_NOTICE.md`
- `CITATION.cff`
- `.gitignore`
- `requirements.txt`
- `code/`
- `outputs/lda/`
- `outputs/qwen/`
- `outputs/graph/`
- `metadata/`
- `figures/lda/`
- `figures/graph/`
- `docs/`

No git repository was initialised and nothing was pushed to GitHub.

## B. Files Copied Into the Package

Code copied into `code/`:

- `Appendix 1.Final Coding Script.ipynb`
- `00_reproduce_current_workflow.ps1`
- `01_local_qwen_metaverse_fincrime_analysis.py`
- `02_write_enhanced_metaverse_fincrime_report.py`
- `03_markdown_to_docx_simple.py`
- `04_write_topic_model_intervention_focus.py`
- `05_build_free_graph_pack.py`
- `README_CODE_EXECUTION.md`

Documentation copied into `docs/`:

- `full_code_listing.md`

Metadata/provenance copied into `metadata/`:

- `LDA_RUN_METADATA_2026-06-25.md`
- `GRAPH_MAPPING_PROVENANCE.md`
- `README_FOR_COAUTHORS.md`
- `workflow_manifest.json`
- `manifest.json`
- `analysis_manifest.json`

Safe figures copied into `figures/lda/`:

- LDA model-selection, topic-prevalence, keyword, heatmap, co-occurrence, wordcloud, and pyLDAvis figure files from `Submission/LDA Model Outputs/`.

Safe graph figures copied into `figures/graph/`:

- `topic_threat_intervention_full.svg`
- `intervention_lifecycle_map.svg`
- `figure_08_framework_graph.svg`

Safe graph tables copied into `outputs/graph/`:

- `graph_edges.csv`
- `graph_edges_with_provenance.csv`
- `intervention_matrix.csv`

## C. Files Excluded and Why

See `docs/EXCLUDED_FILES.md` for the full list. Major exclusions:

- Full-text PDF folders: excluded for copyright/licensing reasons.
- Full extracted text files: excluded because they contain the full corpus text.
- Qwen batch/report files and original document evidence tables: excluded because they contain long source-text snippets or generated prose based closely on those snippets.
- Original `graph_data.json`, `graph_nodes.csv`, graph HTML, document evidence SVG, and GraphML: excluded because they embed document details or evidence snippets.
- Original LDA workbook: excluded because it contains sheets such as `text_export` and `exemplar_chunks`.
- Manuscript drafts: excluded because they are unpublished author documents and not required for the reproducibility package.

## D. Files Redacted or Modified

No original `Submission/` files were modified.

Redacted/derived files created inside the package:

- `outputs/lda/*.csv`: selected safe aggregate sheets extracted from the LDA workbook.
- `outputs/qwen/document_evidence_redacted.csv`: document metadata, evidence counts, relevance labels, and top terms, with long evidence snippets removed.
- `outputs/qwen/aggregate_counts.json`: aggregate Qwen category totals and relevance counts.
- `outputs/graph/graph_nodes_redacted.csv`: graph node metadata with the long `detail` field removed.
- `outputs/graph/graph_data_redacted.json`: graph JSON with document `detail`, `evidence`, and `snippets` fields removed.

Documentation files were newly written for GitHub review:

- `README.md`
- `REPRODUCING.md`
- `DATA_AVAILABILITY.md`
- `LICENSE_NOTICE.md`
- `CITATION.cff`
- `.gitignore`
- `requirements.txt`
- `docs/EXCLUDED_FILES.md`
- `docs/PORTABLE_PATHS_NOTE.md`
- `metadata/QWEN_OLLAMA_MODEL_METADATA.md`

## E. Remaining Issues Before Public Release

1. No open-source license has been selected.
2. Final paper citation, DOI, journal name, and repository URL are placeholders.
3. Exact Ollama version and `qwen2.5:7b` model digest were not available in the supplied files.
4. Several copied Qwen scripts still preserve original Windows/OneDrive paths. This is documented in `REPRODUCING.md` and `docs/PORTABLE_PATHS_NOTE.md`.
5. The author team should confirm that copied figures and redacted outputs are acceptable for public release.
6. The package should be reviewed before any GitHub upload.

## F. Questions for the First Author

1. Which license should govern the code and derived outputs?
2. Can the exact Ollama version and Qwen model digest be recovered?
3. Should `README_FOR_COAUTHORS.md` remain in the public package, or should it be replaced with a less internal-facing provenance note?
4. Should the final repository include the LDA figures in PDF as well as PNG/SVG, or only open/web-friendly formats?
5. What final citation metadata should replace the placeholders in `CITATION.cff`?

## G. Internal Review Safety

The package is safe for internal author/reviewer review before GitHub upload. It avoids copying full-text PDFs, full extracted text, and the main Qwen evidence/report files that contain long verbatim snippets. Public release should wait until the author team approves the license, citation metadata, and final inclusion/exclusion choices.
