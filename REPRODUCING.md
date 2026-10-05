# Reproducing the Analysis

These notes cover the original 59-document analysis (Part 2) and the revised 65-document analysis (Part 1 and the Qwen/graph section). See `README.md` for status and reading limits.

This package supports reproducibility review, but it does not include full-text PDFs or full extracted text. A complete rerun from raw PDFs requires lawful access to the source documents.

This repository contains two separate analyses. **Their environments are incompatible and must be installed separately.** See `docs/VERSIONS.md`.

---

# Part 1 - Revised LDA, 65 documents (2026-09)

Everything in this part lives under `lda_65docs_2026-09/`.

## Environment

The recorded run used Python 3.13.15 on Linux with the pinned versions in `lda_65docs_2026-09/requirements-resolved.txt`, and WordNet 3.0.

```bash
python3 -m venv .venv-65
source .venv-65/bin/activate
pip install -r lda_65docs_2026-09/requirements-resolved.txt
```

Use a separate environment from Part 2. This analysis uses scikit-learn `LatentDirichletAllocation`; the original analysis uses gensim `LdaMulticore` and different pinned versions of numpy, scipy, gensim and matplotlib.

The pipeline downloads WordNet if it is absent, so a first run may need network access. Record any platform, Python or dependency differences. No assertion of identical results across untested environments is made.

## Input corpus

Obtain the 65 original PDF files through the permitted research access route. Preserve the relative filenames recorded in `lda_65docs_2026-09/tables/corpus_manifest.csv` and verify their SHA-256 hashes against that file. The recorded code includes a content-hash-specific page rule for one book chapter; supplying a different file or an edited PDF can change extraction and results.

The corpus manifest records **computational** inclusion. Scientific eligibility, bibliographic accuracy, publication types and quality appraisal are held in separate records; `tables/metadata_template.csv` now has `year` and `screening_id` filled from the study-selection record, but study type is still `unknown` and no appraisal exists; bibliographic metadata and its unresolved items are in `tables/corpus_bibliographic_metadata.csv` and `METADATA_SOURCES_AND_GAPS.md`.

## Running

Either use the notebook `lda_65docs_2026-09/Run_LDA.ipynb`, which writes the script, pinned requirements and configuration into a working directory and then invokes the pipeline, or run the script directly:

```bash
python lda_65docs_2026-09/Metaverse_LDA_Colab.py \
  --input-dir /path/to/the/65_PDFs \
  --output-dir /path/to/lda_results \
  --profile research \
  --config-json lda_65docs_2026-09/run_config.json
```

This is a substantial computation: the research profile performs 165 grouped validation fits, 25 full-corpus fits and 18 sensitivity fits, 208 fits in total. Completed fits are checkpointed, so reusing the same configuration and paths resumes a reproduction. The script writes a `run_<fingerprint>` directory; the fingerprint includes local paths and code bytes, so its name will not match the recorded run identifier.

`--profile smoke` is a smaller plumbing check only. Smoke outputs are not the reported results.

`Run_LDA.ipynb` is a reproduction notebook, not an execution record: it is deposited with no saved execution counts and no saved output cells, and it was not run to prepare the deposited tables and figures.

## Expected checks

With the recorded inputs and settings, compare the corpus dimensions (65 PDFs, 983 pages, 688 modelling units, 8,186 terms), the selected K = 11, medoid seed 2026, 90 outer updates, and the source tables. `lda_65docs_2026-09/verification.json` records internal consistency checks; its own scope statement applies - these are software consistency checks, not evidence of substantive topic validity.

The author team has selected K = 11 as the exploratory working model, with K = 8 as a more parsimonious comparison. Separately from that choice, no coherence-shortlisted candidate passed the declared seed-stability threshold, and `model_selection_decision.json` records `gates_passed: false`; the automatic rule returned K = 11 as a fallback, not a validated optimum. Do not suppress that qualification when reporting, and do not describe K = 11 as stable or verified.

## Source provenance

`lda_65docs_2026-09/source_provenance.json` records that the deposited `Metaverse_LDA_Colab.py` differs from the executed source in exactly two non-analytical items: the module description and a document-link constant. The two files therefore have different SHA-256 values, both recorded there and in `environment_versions.json`. No model was refitted when preparing the deposited material.

## Same-seed sensitivity audit

`lda_65docs_2026-09/tables/paired_sensitivity_summary.csv` and `paired_sensitivity_pairs.csv` compare each sensitivity variant against the **same-seed** saved full-corpus K=11 baseline, rather than against the single representative model. This isolates the specification effect from the seed-to-seed variation.

To regenerate them from a completed run:

```bash
python lda_65docs_2026-09/audit_paired_sensitivity.py \
  --run-dir /path/to/completed/run_directory \
  --output-dir /path/to/paired_audit
```

The helper reads 21 saved models (three baselines and eighteen alternatives) and **fits nothing**. Those model caches are produced by the full research run and are not included in this repository, so the helper cannot be run against this repository alone; the shipped tables can be read without it.

Note on columns: `paired_sensitivity_pairs.csv` carries a `basis` column recording the comparison base for each row. That column is documentation added when the appendix tables were assembled; it is not emitted by `audit_paired_sensitivity.py`. `paired_sensitivity_summary.csv` matches the script's output columns exactly.

`tables/legacy_reference_seed/sensitivity_runs.csv` and `sensitivity_summary.csv` are the earlier comparison against the representative model. They are retained for provenance and use a different comparison base; the two sets of numbers are not interchangeable.

---

# Part 2 - Original analysis, 59 documents (2026-06)

## Environment

The original LDA notebook was prepared for Python 3 and a Colab-style runtime. Package versions are listed in `requirements.txt`.

```bash
python3 -m venv .venv-59
source .venv-59/bin/activate
pip install -r requirements.txt
```

The notebook may download NLTK resources at runtime (`stopwords`, `wordnet`, `omw-1.4`), so a first run may need network access.

## Rerunning the original LDA pipeline

The source notebook is `code/Appendix 1.Final Coding Script.ipynb`.

It is intentionally saved as a clean source notebook, without saved execution counts or output cells. The executed output record is represented here by:

- `metadata/LDA_RUN_METADATA_2026-06-25.md`
- `outputs/lda/*.csv`
- `figures/lda/`

To rerun from PDFs, obtain the source PDFs lawfully and place them in the expected input directory. The original final-run canonical folder was documented as `Submission/kumar_MV`, which is not included here because it contains copyrighted PDFs. If adapting the notebook outside the original environment, update its input path settings.

Known reproducibility caveat for this part only: the notebook uses `LdaMulticore`. Even with random seed 42 and pinned package versions, minor numerical variation can occur across machines, worker counts, and library runtimes. This caveat does not describe the revised analysis in Part 1, which uses a different library and five seeds.

## Using existing derived outputs

- `outputs/lda/` - model diagnostics, topic tables, topic similarity, document-topic probabilities and term-weight tables exported from the submitted workbook.
- `outputs/qwen/aggregate_counts.json` - corpus-level evidence totals and relevance counts.
- `outputs/qwen/document_evidence_redacted.csv` - document metadata, category counts, relevance labels and top counted terms, with long evidence snippets removed.
- `outputs/graph/` - graph edges, provenance, intervention matrix, redacted nodes and redacted graph JSON.

The original LDA workbook is not copied because it includes sheets such as `text_export` and `exemplar_chunks` that may contain extracted text or long token excerpts.

## Rerunning or inspecting the Qwen/Ollama workflow

The local Qwen workflow scripts are in `code/`:

1. `01_local_qwen_metaverse_fincrime_analysis.py`
2. `02_write_enhanced_metaverse_fincrime_report.py`
3. `03_markdown_to_docx_simple.py`
4. `04_write_topic_model_intervention_focus.py`
5. `05_build_free_graph_pack.py`

The PowerShell driver is `code/00_reproduce_current_workflow.ps1`.

What each stage reads, for the avoidance of doubt:

- Script 01 reads a single concatenated extracted-text file (a hard-coded path constant in the legacy script). It does **not** read any LDA output. The four category counts and the relevance classification it produces are generated by keyword rules and fixed thresholds in that script, not by the language model. Qwen is called afterwards, on the material those rules selected, to produce batch summaries and a final synthesis.
- Script 05 reads the evidence table produced by script 01. The seven topic labels and their prevalence values are literal values in `05_build_free_graph_pack.py`; they are not read from `outputs/lda/`. Changing the topic model therefore requires editing that script, not only regenerating inputs.

Local model requirement:

- Ollama local server at `http://localhost:11434/api/generate`
- Model tag `qwen2.5:7b`; model ID and digests in `metadata/QWEN_OLLAMA_MODEL_METADATA.md`
- Generation settings recorded in code: `temperature = 0.2`, `top_p = 0.9`

Exact Qwen prose may vary across environments, hardware and Ollama runtime versions. The Ollama version used for the May 2026 run was not captured in the saved artefacts and could not be recovered later.

The 65-document Qwen workflow and the K = 11 graph are in `qwen_graph_65docs_2026-10/` (see its README for run order, dependencies and what can and cannot be re-executed without the source PDFs). The material in `outputs/qwen/` and `outputs/graph/` is the earlier 59-document version; seven documents of the revised corpus were never processed by it, and one document it processed is no longer in the revised corpus.

## Rerunning or inspecting the 65-document Qwen/graph workflow

Everything is in `qwen_graph_65docs_2026-10/`; its README gives the order `build_input_from_extracted.py` -> `run_rules_stage1.py` -> `run_stage2_qwen.py`, then the graph scripts `01`-`07`. The code uses only the Python standard library except `matplotlib` and `openpyxl` (graph; see `qwen_graph_65docs_2026-10/graph/requirements.txt`).
Absolute paths were replaced by environment variables (`CHBR_SYNC_ROOT`, `CHBR_OLD_REPO_ROOT`, `CHBR_PROJECT_ROOT`, `CHBR_QWEN_INPUT_FILE`). Record versions: Ollama 0.34.2, `qwen2.5:7b` (ID `845dbda0ea48`). A re-run of the model stage produces new text; it is not a reproduction of the recorded output.

## Path configuration

**Original 59-document scripts (`code/`).** They still contain the absolute directory of an author's machine as hard-coded constants, as in the original run. They were not modified. To run them on your own inputs, edit those constants to point to your local directory; the inputs are not distributed (see `DATA_AVAILABILITY.md`) and the result is a new run, not a reproduction of the recorded one.

**Revised 65-document code.** `lda_65docs_2026-09/` takes input and output directories on the command line. `qwen_graph_65docs_2026-10/` uses command-line arguments and the environment variables `CHBR_SYNC_ROOT`, `CHBR_OLD_REPO_ROOT`, `CHBR_PROJECT_ROOT` and `CHBR_QWEN_INPUT_FILE`; the lines that differ from the executed scripts are listed in `qwen_graph_65docs_2026-10/CODE_CHANGE_LOG.md`.

## Known limitations

- Full-text PDFs are not included, for either analysis.
- Full extracted corpus text is not included, for either analysis.
- The revised analysis does not include its fitted model caches, so its same-seed sensitivity helper cannot be run from this repository alone.
- Qwen prose summaries may vary across reruns; the original Ollama runtime version was not captured.
- K = 11 is the selected exploratory working model, with K = 8 as a parsimonious comparison. It did not pass the declared seed-stability threshold and must not be reported as stable or verified.
- The Qwen and graph layer in the repository root is the 59-document version; the 65-document version is in `qwen_graph_65docs_2026-10/`. Its model stage was run once (seed 42 is a prospective setting) and reproduction of the model text is not claimed.
- Historical "pending" statements about the topic-label review in some supplement files predate the completed review record; see `lda_65docs_2026-09/CURRENT_REVIEW_STATUS.md`.
- The revised analysis is deposited without its fitted model caches, so its saved models cannot be reloaded from this repository.
