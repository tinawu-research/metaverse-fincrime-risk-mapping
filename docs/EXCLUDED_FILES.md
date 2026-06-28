# Excluded Files

This package intentionally excludes files that contain copyrighted source documents, full extracted text, or long verbatim excerpts from source PDFs.

## Excluded Source Corpus

- `Submission/PDFs/`
- `Submission/kumar_MV/`

Reason: These folders contain full-text PDFs or extracted book chapters/articles that may be subject to publisher copyright and licensing restrictions.

## Excluded Full Extracted Text

- `Submission/Appendix 4. Extracted Text.txt`
- `Submission/Qwen Assisted Outputs/all_extracted_text_by_pdf.txt`

Reason: These files contain the full extracted text corpus.

## Excluded Original Qwen Evidence Files

- `Submission/Missing Reproducibility Files 2026-06-25/document_evidence_table.csv`
- `Submission/Missing Reproducibility Files 2026-06-25/document_evidence.json`
- `Submission/Missing Reproducibility Files 2026-06-25/qwen_batch_01.md` through `qwen_batch_12.md`
- `Submission/Missing Reproducibility Files 2026-06-25/qwen_batch_summaries.md`
- `Submission/Missing Reproducibility Files 2026-06-25/complete_analysis_report.md`
- `Submission/Missing Reproducibility Files 2026-06-25/enhanced_complete_analysis_report.md`
- `Submission/Missing Reproducibility Files 2026-06-25/journal_article_integrated_mirofish_topic_model_analysis*.md`

Reason: These files contain, or may contain, long extracted evidence snippets and model-generated prose based closely on those snippets. Redacted aggregate versions are provided in `outputs/qwen/`.

## Excluded Original Graph Files with Embedded Snippets

- `Submission/Qwen Assisted Outputs/graph_data.json`
- `Submission/Qwen Assisted Outputs/graph_nodes.csv`
- `Submission/Qwen Assisted Outputs/full_interactive_graph_pack.html`
- `Submission/Qwen Assisted Outputs/document_evidence_network_full.svg`
- `Submission/Qwen Assisted Outputs/graph_data.graphml.xml`

Reason: These files embed document details, evidence snippets, or large graph payloads derived from extracted corpus text. Redacted versions are provided in `outputs/graph/` where feasible.

## Excluded LDA Workbook

- `Submission/Appendix 3. LDA Model Output.xlsx`
- `Submission/LDA Model Outputs/Appendix 3. LDA Model Output.xlsx`

Reason: The workbook includes sheets such as `text_export` and `exemplar_chunks`, which may include extracted text metadata or long model chunk excerpts. Safe aggregate sheets were exported to CSV in `outputs/lda/`.

## Excluded Manuscript Drafts

- `Submission/V1.Draft.docx`
- `Submission/V2.Draft.docx`
- `Submission/V3.Draft.docx`

Reason: Manuscript drafts are not required for a public reproducibility package and may contain unpublished author text.
