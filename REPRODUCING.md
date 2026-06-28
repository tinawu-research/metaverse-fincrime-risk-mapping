# Reproducing the Analysis

This package supports reproducibility review, but it does not include full-text PDFs or full extracted text. A complete rerun from raw PDFs requires lawful access to the source documents.

## Environment

The LDA notebook was prepared for Python 3 and a Colab-style runtime. Package versions pinned in the notebook are listed in `requirements.txt`.

Suggested setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The notebook may download NLTK resources at runtime (`stopwords`, `wordnet`, and `omw-1.4`), so a first run may need network access unless those resources are already cached.

## Rerunning the LDA Pipeline

The source notebook is:

`code/Appendix 1.Final Coding Script.ipynb`

The original submitted notebook is intentionally saved as a clean source notebook, without saved execution counts or output cells. The executed output record is represented here by:

- `metadata/LDA_RUN_METADATA_2026-06-25.md`
- `outputs/lda/*.csv`
- `figures/lda/`

To rerun from PDFs, obtain the source PDFs lawfully and place them in the expected input directory. The original final-run canonical folder was documented as `Submission/kumar_MV`, but that folder is not included here because it contains copyrighted PDFs. If adapting the notebook outside the original environment, update its input path settings.

Known LDA reproducibility caveat: the notebook uses `LdaMulticore`. Even with random seed 42 and pinned package versions, minor numerical variation can occur across machines, worker counts, and library/runtime environments.

## Using Existing Derived Outputs

The package includes selected non-copyrighted or redacted derived outputs:

- `outputs/lda/` contains model diagnostics, topic tables, topic similarity, document-topic probabilities, and term-weight tables exported from the submitted workbook.
- `outputs/qwen/aggregate_counts.json` records corpus-level evidence totals and relevance counts.
- `outputs/qwen/document_evidence_redacted.csv` keeps document metadata, category counts, relevance labels, and top counted terms, but removes long evidence snippets.
- `outputs/graph/` contains graph edges, provenance, intervention matrix, redacted nodes, and redacted graph JSON.

The original LDA workbook is not copied because it includes sheets such as `text_export` and `exemplar_chunks` that may contain extracted text or long token excerpts.

## Rerunning or Inspecting the Qwen/Ollama Workflow

The local Qwen workflow scripts are in `code/`:

1. `01_local_qwen_metaverse_fincrime_analysis.py`
2. `02_write_enhanced_metaverse_fincrime_report.py`
3. `03_markdown_to_docx_simple.py`
4. `04_write_topic_model_intervention_focus.py`
5. `05_build_free_graph_pack.py`

The PowerShell workflow is:

`code/00_reproduce_current_workflow.ps1`

Local model requirement:

- Ollama local server at `http://localhost:11434/api/generate`
- Model tag: `qwen2.5:7b`
- Ollama model ID and digests: see `metadata/QWEN_OLLAMA_MODEL_METADATA.md`
- Generation settings recorded in code: `temperature = 0.2`, `top_p = 0.9`

The model tag, model ID, model-layer digest, and manifest/config digest are recorded in `metadata/QWEN_OLLAMA_MODEL_METADATA.md` for auditability. Exact Qwen prose may still vary across environments, hardware, and Ollama runtime versions. The original Ollama version for the May 2026 run was not captured in the saved artefacts and could not be reliably recovered later.

## Historical Path Caveat

Several original Qwen scripts preserve Windows/OneDrive paths from the first author's run. These are retained as provenance and are not expected to exist on other machines. To rerun, update the path constants or adapt the scripts to point at locally available input files. The full extracted text file is intentionally not included in this public package.

## Known Limitations

- Full-text PDFs are not included.
- Full extracted corpus text is not included.
- Qwen prose summaries may vary across reruns, even with similar settings.
- The Qwen model tag and digests are recorded, but the original Ollama runtime version was not captured.
- Some original scripts require path configuration before rerun.
- This package is suitable for internal/reviewer reproducibility review before GitHub upload, not final public release without author/license approval.
