# Qwen/Ollama workflow and K = 11 topic-threat graph — 65 publications (2026-10)

This directory is self-contained and belongs to the **revised 65-document analysis**. It is separate from the original 59-document material in the repository root, which is unchanged. Topic numbers (T01-T11) have no correspondence with the original T1-T7.

| Folder | Content |
|---|---|
| `qwen_pipeline/` | workflow code (standard library only), keyword-count table without excerpts, request/response index, sanitised descriptions of prompts, configuration and rules; `README.md` gives run order and recorded model configuration |
| `graph/` | graph code, anonymised author-decision tables, graph exports without document excerpts, paper figure, validation records; `README.md` explains the three edge groups |
| `lda_65docs_2026-09/` (sibling directory) | the topic model that the graph's topic nodes come from |
| `DEPENDENCIES_AND_VERSIONS.md`, `CODE_CHANGE_LOG.md`, `SNAPSHOT_LEDGER.csv` | versions with their recorded source; every change to a code copy; source and hash of every file |

**Not deposited:** the 65 source PDFs, extracted text, rule-selected excerpts, prompts that embed excerpts, raw model records, execution logs, the Ollama runtime and model weights. Obtain the PDFs through your own lawful access route and check them against the SHA-256 values in `lda_65docs_2026-09/tables/corpus_manifest.csv`.
Consequence: the extraction, counting, model and graph-rebuild steps cannot be re-executed from this directory alone; the exports and decision tables can be inspected and re-validated.

**Reading limits.** Exploratory analysis. K = 11 did not pass the declared seed-stability threshold. Keyword totals are counts, not densities or evidence-quality scores. The model stage was run once (a formal random-sample consistency check and a repeated-generation stability check were not carried out: a disclosed limitation); the code copies here did not regenerate any Qwen output; no stability or inter-rater analysis of the LLM-assisted synthesis was carried out. Of 544 graph edges only 24 topic-threat relations were reviewed by the authors.
