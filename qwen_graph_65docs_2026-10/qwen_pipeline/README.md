# Qwen/Ollama workflow — 65 publications

Records the workflow that produced the recorded 2026-09-22 Qwen analysis. **Python standard library only** (no third-party packages).
External runtime requirement for the model stage: an Ollama server (0.34.2 for the recorded run) serving `qwen2.5:7b`.

## Order of execution

| Step | Script | Input → output | Needs model? |
|---|---|---|---|
| 0 | (LDA pipeline, in `Electronic_Supplement_A1`) | 65 PDFs → one extracted-text JSON per document (`raw_pages`) | no |
| 1 | `code/build_input_from_extracted.py` | `--extracted-dir`, `--manifest` (corpus manifest) → one concatenated text file (`--out-txt`) plus a build manifest. Fails loudly on any page/word-count mismatch | no |
| 2 | `code/run_rules_stage1.py` | `--script 01_…py --input <concatenated text> --out-dir D --suffix _65` → `document_evidence_table_65.csv`, `document_evidence_65.json`, `manifest_65.json` | no |
| 3 | `code/run_stage2_qwen.py` | `--script 01_…py --evidence-json … --preflight-manifest … --input-txt … --out-dir …` (`--endpoint`, `--seed 42`, `--resume`) → 13 batch request/response pairs, 1 final-synthesis pair, run record | **yes** |
| 4 (optional) | `code/summarise_stage2.py <qwen_out_dir> <log_dir> <job_id>` | completion/coverage summary from recorded files; reads the identity-check file written by the job | no |

`code/01_local_qwen_metaverse_fincrime_analysis.py` holds the keyword lexicons, the counting/relevance/excerpt-selection rules and the two prompt
templates (`build_batch_prompt`, `build_final_prompt`). It is imported by steps 2 and 3, not run directly. Its `INPUT_FILE` constant (used only by its own
`main()`) now reads the optional environment variable `CHBR_QWEN_INPUT_FILE`; see `../CODE_CHANGE_LOG.md`.

## What the model saw (read this before describing the method)

* Python rules generate the keyword counts and the 17/48 relevance split (17 "primary financial-crime/crypto evidence", 48 "highly relevant platform/security evidence").
* Qwen does **not** read LDA output and does **not** receive full paper text: each batch prompt contains lexicon counts and up to 5–7 rule-selected short extracts per document;
  the final synthesis prompt contains only the 13 batch summaries plus aggregate statistics and top-20 document metadata.
* The analysis ran as 13 batches (5 documents each) and 1 final synthesis = 14 generations.

## Recorded model configuration

| Item | Value |
|---|---|
| Model tag / Ollama ID | `qwen2.5:7b` / `845dbda0ea48` (tag digest `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`) |
| Weights | GGUF Q4_K_M, 7.6 B parameters, model-layer digest `sha256:2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730` |
| Ollama version | 0.34.2 |
| Options, batches | temperature 0.2, top_p 0.9, num_ctx 32768, num_predict 1800, seed 42 |
| Options, final synthesis | same, num_predict 4200 |
| Seed | 42 is a prospective setting for this run; it does not reconstruct the earlier 2026-05 run, and does not guarantee verbatim reproduction on other hardware or Ollama versions |
| Endpoint | per-job loopback port on the compute node (`127.0.0.1:<port>/api/generate`); the script's default `localhost:11434` constant was not used |
| Run | 2026-09-22, 13/13 batches and final synthesis finished with `done_reason = stop`, no retries; every one of the 65 documents covered exactly once |

## Descriptions in `docs/`

Sanitised delivery copies of the pipeline description, the complete prompt templates and run configuration, the rule/code description, the outputs-and-verification index, the keyword-count note and the run conditions. Scheduler/account/host identifiers and author names were removed; project-relative paths in them name files of the project working directory, not files of this delivery.

## What can be re-executed from the shared files, and what cannot

* From `derived/` you can read the keyword counts and the batch↔document mapping and check request/response digests against the index.
* Steps 0–3 need the 65 PDFs (lawful access required; **not distributed**). Step 3 additionally needs a running Ollama with the model above and produces new,
  not identical, text: LLM output reproduction is not claimed.
* Checked on the server on 2026-10-05 (existing files read only): step 2, run with Python 3.12.0 on the existing 65-document concatenated input and the path-parametrised copy of `01_…py`, regenerated `document_evidence_65.json` and `document_evidence_table_65.csv` with SHA-256 identical to the recorded files (recorded originally under Python 3.6.15). These two are the original, excerpt-bearing rule outputs and are **not** delivered; the delivered `derived/document_keyword_counts_65_no_excerpts.csv` is a column projection of the second one and has its own hash. The check covers the deterministic counting rules only; no model generation was re-executed (the original Qwen run of 2026-09-22 is complete; the parametrised/delivery code copies were not used to produce any model output), and the model-stage entry point (`run_stage2_qwen.py`) was checked only for argument parsing and imports, not executed.

## Files in `derived/`

* `document_keyword_counts_65_no_excerpts.csv` — step-2 table without the three `top_evidence_*` excerpt columns (65 rows). Counts are lexicon-hit totals
  per category; they are not densities or quality scores.
* `02_batch_document_mapping.csv` — which five documents each batch covered.
* `02_request_response_index.csv` — SHA-256, byte size, `done_reason` and token counts of each request/response file (the request records themselves are in the separate `qwen_run_records` attachment, as copies with the input-paper excerpts omitted).
