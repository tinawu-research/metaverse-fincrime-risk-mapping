# Changes in the README delivery copy

Original file: `README.md` of the supplement, SHA-256 `0413b62374aa78bf159c3e1fc52f70d8e035286a832554b633586ca942fa1f0a`. Everything not listed here is identical.

## 1. Line replaced

```diff
-- `human_review/`: independent coder and adjudication templates, all uncompleted.
+- `human_review/`: **not part of this delivery.** The historical blank working copies are superseded by the completed topic-label review summarised in `CURRENT_REVIEW_STATUS.md` and `topic_label_review_anonymised.csv`.
```

## 2. Paragraph replaced and extended

```diff
-Appendix B provides provisional evidence cards. Independent ratings, source-to-label adjudication and methodological quality appraisal remain pending. The human-review CSVs are templates, not completed validation records.
+Appendix B provides provisional evidence cards. The topic-label review has since been completed (two reviewers' separate ratings, then label adjudication); see `CURRENT_REVIEW_STATUS.md`. That record does not include a page-by-page source check or a methodological quality appraisal, calculates no inter-rater coefficient, and is not a validation of the topic model or of K = 11. `tables/human_validation_status.json`, the `independent_human_validation` column of `tables/appendix_b_evidence_records.csv` and the "human interpretability ... pending" note in `model_selection_decision.json` are historical run-time records and do not describe the current label-review status; `gates_passed: false` is unchanged.
+
+`audit_paired_sensitivity.py` writes five columns; the delivered `tables/paired_sensitivity_pairs.csv` has a sixth, `basis`, documenting the comparison base of each row. That column was added when the appendix tables were assembled and is not produced by the script. `tables/reviewer_response_crosswalk.csv` is a historical working table and is not part of this delivery.
+
+In this delivery `tables/metadata_template.csv` has `year` and `screening_id` filled from the study-selection record and a new `tables/corpus_bibliographic_metadata.csv` gives the bibliographic fields of the 65 publications; study type stays `unknown` and no quality appraisal exists (see `METADATA_SOURCES_AND_GAPS.md`).
```

## 3. Header

A two-line delivery note was added at the top.
