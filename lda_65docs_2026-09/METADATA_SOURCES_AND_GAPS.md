# Bibliographic metadata for the 65 publications: sources, matching and gaps

`tables/corpus_bibliographic_metadata.csv` (65 rows) and the filled `tables/metadata_template.csv` were compiled **only from records that already existed**: the supplement's `corpus_manifest.csv` (the 65 documents and their SHA-256), Supplementary Table S1 (sheet "Final included studies": the 65 final included records with title, authors, year, source title, DOI, language, database document type, retrieval timing and publication ID), and the Drive-verified final titles list (cross-check). No search was run, and no study type or quality appraisal was started.

| Field | Source | Status |
|---|---|---|
| `document_id`, `filename`, `pdf_sha256`, `page_count` | `corpus_manifest.csv` | complete (65) |
| `title`, `authors_as_recorded`, `year`, `source_title`, `doi`, `retrieval_timing_S1`, `publication_id_S1` | S1 "Final included studies" | complete except where listed below; authors are as recorded in S1 (abbreviated forms), not re-checked against the PDFs |
| `document_type_database_record` | S1 (bibliographic-database label: Article 29, Book chapter 9, Conference paper 18, Proceedings Paper 3, Review 5, research-article 1) | **a database label, not a verified study type** |
| `publication_type`, `type_verified` (template) | — | left `unknown` / `False`: no verified study type exists on the server, none was assigned |
| `quality_appraisal_tool`, `quality_appraisal_result` | — | empty: no appraisal exists |
| `title_in_drive_final_titles_list`, `title_category_drive_list` | Drive-verified `Final_Titles_List` | all 65 titles found; category label as in that list |
| `in_earlier_59_document_corpus` | preflight overlap / added-document tables | 58 yes, 7 no (added) |
| `match_score`, `unresolved_or_notes` | this compilation | each manifest document was matched one-to-one to an S1 record by title words in the file name and in the first 6,000 characters of its extracted text; interlibrary-loan scans were matched from the chapter title in the loan slip |

## Cross-checks
* Against the earlier citation crosswalk (12 documents with APA reference and DOI): 1 unresolved DOI/year difference(s) - D6486a0b043d4 year: crosswalk 2024 vs S1 2023. (A DOI that differs only in hyphenation of the ISBN part is treated as the same DOI.)
* All 65 S1 titles also occur in the Drive-verified final titles list.

## Unresolved items (not guessed)
* `language_as_recorded` is empty for 16 records (S1 does not record it for them).
* DOI missing in S1 for 1 records.
* `Df993b1e11c98`: the PDF file is named "Cryptocurrency in the metaverse" but the loan slip and S1 give the chapter title "Cryptography in the metaverse: advanced protocols for secure communication"; the publisher catalogue year (2024) differs from S1 and the slip (2025). 2025 kept as recorded; unresolved.
* Authors are shown as recorded in S1 (Scopus-style abbreviations); full names, ORCID and affiliations were not compiled.
* The `Record URL`, abstract and author-keyword fields of S1 were not copied.
* Study type (primary study / review / other), publication-type sensitivity and quality appraisal remain **not done**; the template columns for them stay empty or `unknown`.
