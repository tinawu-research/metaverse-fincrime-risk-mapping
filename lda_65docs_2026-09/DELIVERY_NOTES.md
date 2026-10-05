# LDA (65 publications) - delivery notes for the topic-model supplement

The topic-model part of the analysis is the self-contained supplement package (96 files in the recorded state). `A1_FILE_LIST.csv` lists every file of that package with its path *inside the package*, size, SHA-256 and what happens to it in the delivery:
90 files copied as they are, 2 files replaced by delivery copies (`README.md` from `A1_README_delivery_copy.md`, differences in `A1_README_delivery_copy.changes.md`; `tables/metadata_template.csv` from `tables/metadata_template.csv` of this folder),
4 files omitted (three historical working copies of the review workbooks and one superseded crosswalk table). In the assembled supplement the files of this folder sit at its root (`tables/...` files in `tables/`).

* Code entry: `Metaverse_LDA_Colab.py --input-dir <65 PDFs> --output-dir <out> --profile research --config-json run_config.json` (or `Run_LDA.ipynb`). Pinned dependencies: `requirements-resolved.txt`; recorded environment: `environment_versions.json`.
* Inputs not delivered: the 65 source PDFs (obtain lawfully; `tables/corpus_manifest.csv` gives file names, SHA-256 and page counts).
* Current status of the run, the working-model choice, the topic-label review and the topic-threat review: `CURRENT_REVIEW_STATUS.md`. Anonymised label review: `topic_label_review_anonymised.csv`.
* Bibliographic metadata of the 65 publications: `tables/corpus_bibliographic_metadata.csv`; sources and unresolved items: `METADATA_SOURCES_AND_GAPS.md`.
* The supplement's own historical records are unchanged. K = 11 did not pass the declared seed-stability threshold (`gates_passed: false`); nothing in this folder validates the topic structure.
* Reviewer codes: Reviewer A and Reviewer B are the two authors who carried out both the topic-label review and the topic-threat review. "Author C" appears only where a text refers to a passage or table supplied by another author; it is not a reviewer.

**Layout in this repository.** The files are deposited flat, as in the supplement package. The delivery copy of the supplement README is `README_supplement.md` (this directory's `README.md` is the repository README); the two earlier-comparison tables `sensitivity_runs.csv` and `sensitivity_summary.csv` are in `tables/legacy_reference_seed/` (see the README.txt there). `A1_FILE_LIST.csv` and `A1_README_delivery_copy.changes.md` use the supplement's own paths and file names.
