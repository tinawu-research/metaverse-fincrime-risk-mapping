# Metaverse/Crypto Paper Reproducibility Clarifications

Prepared: 2026-06-25

This note addresses the reproducibility and packaging issues raised for the metaverse and cryptocurrency financial-crime paper. The issues found are packaging/documentation issues, not result mismatches.

## Short Status

| Issue | Status | Action |
|---|---|---|
| Missing Qwen intermediate files | Files exist in the analysis run folder but not all are visible in the submission-side shared folder. | Copy the intermediate Qwen files into `Submission/Qwen Assisted Outputs/intermediate_qwen_run_20260527-112059/`. |
| `analysis_manifest.json` | No file with that exact name was found. The Qwen script writes `manifest.json`; the reproducibility package also has `workflow_manifest.json`. | Include `manifest.json`, `workflow_manifest.json`, and an alias copy named `analysis_manifest.json` to avoid confusion. |
| Hard-coded Windows/OneDrive paths in Qwen code | Confirmed in the exact code listing. | Preserve the exact original code for audit, and add portability notes explaining how to rerun using relative paths or a changed base directory. |
| LDA notebook has no saved outputs | Confirmed: 25 code cells, zero saved execution counts, zero saved outputs. | Treat the notebook as a clean source notebook; include this run metadata note plus the exported workbook and figure folder as the execution-output record. |
| Duplicate PDF folders | `Submission/PDFs` and `Submission/kumar_MV` both contain 59 PDFs with identical names and byte sizes as checked on 2026-06-25. | Declare `Submission/kumar_MV` as the canonical input folder for the final run, with `Submission/PDFs` as a duplicate/convenience copy. |
| Graph construction provenance | Current graph CSV has relation labels but no separate provenance column. | Add graph provenance note distinguishing rule-generated document edges from interpretive topic/threat/intervention mappings requiring author review. |

## Canonical Files To Share

Core submission files:

- `Submission/Appendix 1.Final Coding Script.ipynb`
- `Submission/Appendix 2. Qwen synthesis code.md`
- `Submission/Appendix 3. LDA Model Output.xlsx`
- `Submission/Appendix 4. Extracted Text.txt`
- `Submission/LDA Model Outputs/`
- `Submission/Qwen Assisted Outputs/`

Additional files to make visible in the shared submission folder:

- `document_evidence_table.csv`
- `document_evidence.json`
- `manifest.json`
- `analysis_manifest.json` (alias copy of `manifest.json`)
- `qwen_batch_01.md` through `qwen_batch_12.md`
- `qwen_batch_summaries.md`
- `complete_analysis_report.md`
- `enhanced_complete_analysis_report.md`
- `topic_model_emerging_threats_modelling_intervention_focus.md`
- `topic_model_threat_intervention_framework.mmd`
- `journal_article_integrated_mirofish_topic_model_analysis.md`
- `journal_article_integrated_mirofish_topic_model_analysis_SUBAGENT_APPROVED.md`
- `journal_article_integrated_mirofish_topic_model_analysis_subagent_review_trail.md`
- `journal_article_integrated_mirofish_topic_model_analysis_subagent_review_trail.json`
- `journal_reproducibility_package/`
- `graph_edges_with_provenance.csv` (derived from `graph_edges.csv` with added provenance and submission-caution columns)

## Suggested Manuscript/Appendix Clarification

The analysis proceeded in three distinct stages. First, the corpus of 59 PDFs was processed in Python and modelled using LDA topic modelling. Second, the topic-model outputs and extracted corpus evidence were interpreted using a locally hosted Qwen 2.5 model via Ollama/MiroFish as an interpretive aid; this stage did not use a paid API. Third, a transparent graph layer connected topics, evidence dimensions, threat environments, analytical signals, and intervention points. Document-to-evidence and document-to-threat edges were generated using rule-based keyword matching against titles and evidence snippets, while topic-to-threat and threat-to-intervention mappings were interpretive conceptual mappings for author review rather than direct LDA outputs.

## Notes For Submission

- The absence of saved outputs in the notebook should be explained as a notebook-packaging choice, not as missing results. The executed outputs are preserved in `Appendix 3. LDA Model Output.xlsx` and in the `LDA Model Outputs` figures.
- The absolute paths in the Qwen code should be retained in the exact code appendix for auditability, but the reproducibility note should explain that another user needs to update the base path to their local folder or use the copied reproducibility package.
- The two PDF folders should not both be described as separate corpora. They are duplicate copies of the same 59-file corpus.
