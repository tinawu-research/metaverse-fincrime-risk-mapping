# LDA (65 publications): current status, and what the historical files do and do not say

**Delivery document, 2026-10-05.** The original supplement files, their run records and their hashes are kept unchanged. This note states the current status
so that historical "pending" wording in them is not mistaken for the current label-review status. Four separate things must not be merged:

| # | Matter | Current status | Where recorded |
|---|---|---|---|
| 1 | **What the analysis run recorded** (2026-09, 65 publications, scikit-learn LDA) | K = 11 (medoid seed 2026) was returned by the declared selection rule as a **fallback after the seed-stability gate failed**: `gates_passed: false`. Full-corpus matched seed similarity at K = 11 is about 0.39 against the declared threshold of 0.70. The record is a run-time snapshot and is **not** changed. | `model_selection_decision.json`, `tables/full_corpus_seed_stability.csv`, `source_provenance.json` |
| 2 | **Choice of working model** | The author team selected K = 11 as the *exploratory working model* and retained K = 8 as a more parsimonious comparison. This choice is made; it does not remove the stability qualification in row 1. | this note; supplement README |
| 3 | **Topic-label review** (are the eleven keyword-derived labels acceptable?) | **Completed.** Two reviewers (Reviewer A and Reviewer B, the same two authors who carried out the topic-threat review) recorded separate decisions, proposed labels and 1-5 confidence scores for all 11 topics; the final labels were then agreed by adjudication (consolidated record date 2026-09-18; the workbooks were last modified on 2026-09-22). All eleven topics were accepted by both reviewers; the adjudicated labels are in `topic_label_review_anonymised.csv`. The independence of the pre-discussion ratings rests on the authors' attestation recorded in the workbooks (`Start_here`), not on anything verifiable from the files. **No inter-rater coefficient was calculated and none is inferred here.** The record does not document a separate page-by-page check of sources or quotations, and it is not a validation of the topic model. | `topic_label_review_anonymised.csv` (this delivery); original workbooks retained internally |
| 4 | **Topic-threat review** (graph) | A separate review of 34 candidate topic-threat pairs; 24 retained. Unrelated to the label review and to model stability. | `graph/` in this delivery |

## Which workbooks are current
The current label-review record is the set of three workbooks `coder_1_topic_review.xlsx`, `coder_2_topic_review.xlsx` and `label_adjudication.xlsx`
(Drive modification date 2026-09-22; downloaded 2026-09-28 and cross-checked: coder sheets and adjudication sheet agree cell by cell for all 11 topics):

| Workbook | SHA-256 |
|---|---|
| `coder_1_topic_review.xlsx` | `1148ab2595d296420bd0e477df917d32a3a6fe6abeb42f47daa84fd342f286db` |
| `coder_2_topic_review.xlsx` | `e26988951cde9fba892d1ae52502a10013f08eab934352b8c6368cd40bfd2566` |
| `label_adjudication.xlsx` | `96f9b7795f91a6a5567b0031cc47ce7a398676ac00a61e02e23753674c86f2ba` |

The workbooks name the reviewers; they are kept internally. This delivery gives the anonymised transcription instead. The three older files in the supplement's `human_review/` folder
(earlier versions whose `Start_here` text says that ratings and confidence scores were "not supplied") are **historical only**, represent nothing about the current review and are not part of this delivery.

Their `Start_here` sheets state, in the authors' words (names replaced by reviewer codes): "Independent human topic ratings were completed separately by Reviewer A and Reviewer B for all 11 topics before discussion. Their separate records were retained, and final labels were agreed through adjudication." and, on scope:
"The independent topic-rating record does not by itself document a separate page-by-page source or quotation check; Appendix B retains the source locators and interpretive limits."

Whether Appendices A and B and the supplement README were aligned with these completed records was not independently checked in this delivery; the README delivery copy was edited for that reason (see below).

## Historical files that still contain "pending" wording (kept unchanged, not current status)
| File | What it says | How to read it |
|---|---|---|
| `model_selection_decision.json` (note 2) | "Human interpretability checks by at least two coders remain pending until completed rating files are supplied." | Run-time wording from the analysis run. Superseded **for label review only** by row 3. `gates_passed: false` and the first note remain current. |
| `tables/human_validation_status.json` | `status: pending`, `ratings_computed: false` | Run-time placeholder. Not the current label-review status. |
| `tables/appendix_b_evidence_records.csv`, column `independent_human_validation` = `pending` (33 rows) | placeholder per evidence card | Describes the evidence-card table when it was generated, not the label review. Source-to-label page checks are not claimed. |
| `human_review/*.xlsx` (not delivered) | older working copies | Historical only. |

Nothing in this note changes `gates_passed`, any numerical result, or the provisional status of K = 11.
