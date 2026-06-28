# LDA Run Metadata

Prepared: 2026-06-25

## Purpose

This note documents the LDA run metadata because `Appendix 1.Final Coding Script.ipynb` is saved as a clean source notebook without execution outputs.

## Notebook Output Status

- Notebook: `Submission/Appendix 1.Final Coding Script.ipynb`
- Total cells: 31
- Code cells: 25
- Code cells with saved execution counts: 0
- Code cells with saved outputs: 0
- Kernelspec: Python 3

This means the notebook is not self-showing as an executed notebook. The execution-output record is instead held in the exported workbook and generated figure files.

## Output Record

- Workbook: `Submission/Appendix 3. LDA Model Output.xlsx`
- Figure/output folder: `Submission/LDA Model Outputs/`
- Extracted text file: `Submission/Appendix 4. Extracted Text.txt`

The workbook contains the model-selection, selected-model, topic-summary, document-topic, diagnostic, and quality-metric sheets. The figure folder contains the exported model-selection, topic-prevalence, keyword, heatmap, co-occurrence, wordcloud, and pyLDAvis outputs.

## Input Corpus

- Canonical PDF folder for final run: `Submission/kumar_MV`
- Duplicate/convenience copy: `Submission/PDFs`
- Verification on 2026-06-25: both folders contained 59 PDFs with identical filenames and byte sizes.
- Extracted text file used for downstream synthesis: `Submission/Appendix 4. Extracted Text.txt`

## Key Notebook Configuration

- `RUN_MODE = "upload_pdfs"`
- `PDF_DIR = Path("/content/pdfs")`
- `DRIVE_PDF_DIR = "/content/drive/MyDrive/kumar_MV"` when drive mode is used
- `gensim==4.3.3`
- Model class: `LdaMulticore`
- `RANDOM_STATE = 42`
- `CHUNK_SIZE = 900`
- `CHUNK_OVERLAP = 100`
- `MIN_CHUNK_TOKENS = 150`
- `TOPIC_RANGE = range(3, 9)`
- `LDA_PASSES = 12`
- `LDA_ITERATIONS = 250`
- `NO_BELOW = 4`
- `NO_ABOVE = 0.45`
- `MAX_CHUNKS_PER_DOCUMENT_FOR_MODEL = 50`

## Selected Model Metrics

Verified from `Appendix 3. LDA Model Output.xlsx`:

- Selected topic count: 7
- c_v coherence: 0.4185741840510382
- Perplexity: 275.0294678443901
- Log-likelihood bound: -1596070.223483145

## Packaging Recommendation

For journal submission, either provide an executed notebook or include this run metadata file with the workbook and figures. The latter is sufficient if the appendix clearly states that the notebook is a source notebook and that the executed outputs are preserved separately.
