# Version map

This repository holds two topic-modelling analyses. Nothing from the original analysis has been moved or renamed, so all existing paths and links remain valid. This file records which files belong to which version.

## Original analysis - 59 documents, seven topics (2026-06)

Implementation: gensim `LdaMulticore`, single seed 42, candidate K = 3 to 8.
Dependencies: `requirements.txt`.

| Path | Notes |
|---|---|
| `code/Appendix 1.Final Coding Script.ipynb` | Original LDA notebook. Clean source notebook, no saved outputs |
| `code/00_reproduce_current_workflow.ps1` | Driver for the Qwen and graph stages |
| `code/01_local_qwen_metaverse_fincrime_analysis.py` | Rule-based evidence pass, then local Qwen summarisation |
| `code/02_write_enhanced_metaverse_fincrime_report.py` | Report writer |
| `code/03_markdown_to_docx_simple.py` | Format conversion |
| `code/04_write_topic_model_intervention_focus.py` | Intervention-focus write-up. Model statistics are literal values in the script |
| `code/05_build_free_graph_pack.py` | Graph builder. The seven topic labels and prevalence values are literal values in the script, not read from `outputs/lda/` |
| `outputs/lda/` | Aggregate topic-model outputs, 59 documents, seven topics |
| `outputs/qwen/` | Redacted evidence summaries, 59 documents |
| `outputs/graph/` | Graph edges, nodes, provenance and intervention matrix |
| `figures/lda/`, `figures/graph/` | Figures for this version |
| `metadata/` | Run metadata, manifests and provenance notes for this version. The manifests record `document_count: 59`; these are historical run records and are deliberately left unchanged |
| `requirements.txt` | Dependencies for this version only |

## Revised LDA - 65 documents, eleven topics (2026-09)

Implementation: scikit-learn `LatentDirichletAllocation`, five seeds, candidate K = 2 to 12. K = 11 selected as the exploratory working model, K = 8 as a parsimonious comparison; the seed-stability gate was not passed.
Dependencies: `lda_65docs_2026-09/requirements-resolved.txt`.

Everything for this version is under `lda_65docs_2026-09/`. See that directory's `README.md`.

## Relationship between the two

- The corpora overlap in **58** documents.
- One document appears only in the 2026-06 corpus: `Metaverse_ ethical challenges of the tokenisation of the economy_NON_ENGLISH_PAPER_compressed.pdf`.
- Seven documents appear only in the 2026-09 corpus, and **none of them was processed by the original (59-document) Qwen or graph stage; they are processed in the 65-document layer**: `Classification of NFT Security Issues and Threats through Case Analysis.pdf`, `Cryptocurrency in the metaverse.pdf`, `Cyber security vulnerabilities and threat mitigation strategies.pdf`, `GenAI with custom trained.pdf`, `Innovative Accounting and Auditing.pdf`, `Is the metaverse failing.pdf`, `Payment System Vulnerabilities.pdf`.
- The screening rationale for these changes is held in the corpus-selection records, not in this repository.

## Topic numbering

**The two versions' topic numbers have no correspondence.** Original T1-T7 and revised T01-T11 come from different corpora, different vocabularies, different implementations and different seeds. Do not map one onto the other by number, and do not renumber one to match the other. Any comparison must be made on topic content, with the evidence stated.

## Dependencies

`requirements.txt` and `lda_65docs_2026-09/requirements-resolved.txt` are not interchangeable and must not be merged. They pin incompatible versions of numpy, scipy, gensim and matplotlib, and only the revised analysis uses scikit-learn. Install each into its own environment.

## Qwen and graph layer

The version in the repository root (`code/01-05`, `outputs/qwen/`, `outputs/graph/`, `figures/graph/`) belongs to the original 59-document analysis and is kept unchanged.

The Qwen evidence pass and the K = 11 topic-threat graph for the final 65-document corpus are in `qwen_graph_65docs_2026-10/`: 13 batches plus one final synthesis with `qwen2.5:7b`; keyword counts and the 17/48 relevance split come from Python rules; the model did not read the topic-model output and did not receive full paper text. The graph has 118 nodes and 544 edges: 24 author-reviewed topic-threat relations, 447 rule-generated document relations and 73 fixed conceptual links carried over from the earlier implementation. The seven documents that appear only in the 2026-09 corpus are processed there.
Original raw model outputs are not deposited here; see `qwen_graph_65docs_2026-10/README.md` for what is.
