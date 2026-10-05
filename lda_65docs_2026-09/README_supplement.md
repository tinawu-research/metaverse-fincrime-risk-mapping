> Delivery copy of the supplement README (2026-10-05); the original is unchanged. Changed passages are marked in `A1_README_delivery_copy.changes.md`.

# Electronic Supplement A1 — LDA analysis of 65 publications

This supplement accompanies Appendix A (computational methods) and Appendix B (topic evidence). It contains the complete analytical implementation and selected recorded outputs. It contains no Qwen implementation. No new topic models were fitted in preparing this package.

## Files

- `Metaverse_LDA_Colab.py`: complete pipeline version 1.0.1.
- `Run_LDA.ipynb`: self-contained notebook with embedded script, configuration and requirements. Its archive/export step has no external helper dependency.
- `run_config.json`: recorded research configuration; input/output paths are supplied at execution.
- `requirements-resolved.txt`: complete recorded Python package snapshot.
- `environment_versions.json`: actual recorded execution environment, including original source hash.
- `source_provenance.json`: original and distributed source hashes and the two preparation changes. Analytical syntax trees match after excluding the module description and document-link constant. Run paths/hashes can change without changing the analysis.
- `audit_paired_sensitivity.py`: same-seed comparison of saved baseline and alternative K=11 fits; performs no fitting.
- `tables/`: corpus manifest/hashes, transformations, numerical diagnostics, topic/source records and quote-location checks.
- `figures/`: PNG, SVG and PDF outputs. Appendix A uses S1 convergence and S2 unit counts; Appendix B uses S3 prevalence and S4 publication mixtures.
- `human_review/`: **not part of this delivery.** The historical blank working copies are superseded by the completed topic-label review summarised in `CURRENT_REVIEW_STATUS.md` and `topic_label_review_anonymised.csv`.

## Environment

The recorded run used Python 3.13.15 on Linux, the package versions in requirements-resolved.txt, and WordNet 3.0. A local recreation should use a separate environment. The pipeline downloads WordNet if it is missing; installation/resource download therefore requires network access. Record any platform, Python or dependency differences. No assertion of identical results across untested environments is made.

From this supplement directory:

```text
python -m venv .venv
```

Activate the environment using the command appropriate to your operating system, then:

```text
python -m pip install -r requirements-resolved.txt
python Metaverse_LDA_Colab.py --help
```

## Input corpus

Obtain the 65 original PDF files through the permitted research access route. Preserve the relative filenames recorded in tables/corpus_manifest.csv and check their SHA-256 hashes. Full-text PDFs and long extracted passages are not distributed in this supplement. The recorded code includes the content-hash-specific page rule for one chapter. Supplying a different file or edited PDF can change extraction and results.

The corpus manifest records computational inclusion. Scientific eligibility, bibliographic accuracy, publication types and quality appraisal must be checked in their own records; metadata_template.csv is not a completed appraisal.

## Research execution

The full configuration performs 165 grouped validation fits, 25 full-corpus fits and 18 sensitivity fits (208 fits in total for the recorded run). This is substantial computation. The commands below are reproduction instructions; they were not run to prepare the appendices.

```text
python Metaverse_LDA_Colab.py --input-dir /path/to/the/65_PDFs --output-dir /path/to/lda_results --profile research --config-json run_config.json
```

Replace the two directory values. Do not supply invented study-type metadata. If verified metadata or page rules are deliberately added, record the changed specification. The script writes a run_<fingerprint> directory under the selected output directory and caches completed fits. The fingerprint includes local paths, software and code bytes, so its directory name need not match the recorded run identifier. Reuse the same configuration/paths to resume that reproduction's checkpoints.

Use `--profile smoke` only for a deliberate, smaller plumbing check. Smoke outputs are not the reported scientific results. Neither research nor smoke fitting was launched during appendix preparation.

## Expected checks

With the recorded inputs/settings, compare the corpus dimensions (65 PDFs, 983 pages, 688 units, 8,186 terms), selected K=11, medoid seed 2026, 90 outer updates and source tables. The recorded recommendation is provisional because no coherence-shortlisted candidate passed the seed-stability threshold. Do not suppress this qualification. Numerical consistency checks do not validate substantive labels.

## Same-seed sensitivity audit

The base pipeline's original sensitivity comparison uses the representative model. To reproduce Appendix A's matched-seed table, use the following separate command against the completed run's saved model caches:

```text
python audit_paired_sensitivity.py --run-dir /path/to/completed/run_directory --output-dir /path/to/paired_audit
```

The helper reads 21 saved models (three baselines and eighteen alternatives) and does not fit models. Use the study's own saved or reproduced cache files. These caches are not included in this supplement; they are generated by the full research run. The results shipped in tables/paired_sensitivity_*.csv can be examined without rerunning or loading caches.

## Outputs and sharing

The pipeline also creates a private output directory containing extracted full text, model caches and human-review working materials. Its generated derived-output archive excludes that private directory. Review files before any deposition; this prepared supplement itself has not been uploaded or published. Corpus access and copyright conditions are separate from access to the code and derived records.

Appendix B provides provisional evidence cards. The topic-label review has since been completed (two reviewers' separate ratings, then label adjudication); see `CURRENT_REVIEW_STATUS.md`. That record does not include a page-by-page source check or a methodological quality appraisal, calculates no inter-rater coefficient, and is not a validation of the topic model or of K = 11. `tables/human_validation_status.json`, the `independent_human_validation` column of `tables/appendix_b_evidence_records.csv` and the "human interpretability ... pending" note in `model_selection_decision.json` are historical run-time records and do not describe the current label-review status; `gates_passed: false` is unchanged.

`audit_paired_sensitivity.py` writes five columns; the delivered `tables/paired_sensitivity_pairs.csv` has a sixth, `basis`, documenting the comparison base of each row. That column was added when the appendix tables were assembled and is not produced by the script. `tables/reviewer_response_crosswalk.csv` is a historical working table and is not part of this delivery.

In this delivery `tables/metadata_template.csv` has `year` and `screening_id` filled from the study-selection record and a new `tables/corpus_bibliographic_metadata.csv` gives the bibliographic fields of the 65 publications; study type stays `unknown` and no quality appraisal exists (see `METADATA_SOURCES_AND_GAPS.md`).

The original sensitivity_runs.csv and sensitivity_summary.csv are preserved for provenance. They compare with the representative seed; Appendix A Table A2 uses paired_sensitivity_summary.csv instead. Do not interchange these comparison bases. The interactive pyLDAvis display is also supplied; its areas are token-weighted, not the equal-publication prevalence used in the manuscript.
