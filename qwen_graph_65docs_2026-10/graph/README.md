# K=11 topic–threat graph — 65 publications

**118 nodes, 544 edges.** Node types: topic 11, threat 9, layer 7, signal 9, intervention 13, evidence dimension 4, document 65.
Edge origins — keep these three apart in any description:

| `edge_origin` | Edges | Meaning |
|---|---|---|
| `author_reviewed_k11_20261001` | **24** | topic–threat associations the authors reviewed and kept (34 candidate pairs reviewed; 10 excluded; T03 has none) |
| `rule_65docs` | 447 | rule-generated document relations from lexicon counts (251 document→dimension, 193 `document-keyword-matches-threat`, 3 `high-score-keyword-anchor`); not author-reviewed |
| `legacy_fixed_concept` | 73 | fixed threat→layer/signal/intervention and layer/signal→detection→control links carried over from the 2026-06 implementation; not reviewed in this round |

The 24 is **not** the total edge count. Only the 24 topic–threat edges were in the authors' review scope.
The topic–threat edges are thematic associations supported by selected corpus passages; they do not estimate crime incidence, establish causation, or demonstrate that any control is effective.
Topic proportions are mean publication-level topic weights (thematic attention), not crime rates. T01/T06 associations are perception-based; T04 is limited to trust/reputation-system attacks; T10 is a potential (quantum) risk;
the Manning NFT finding is a caveat on the T08→DeFi association. T06 and T09 are kept as separate topics.

## How the three edge groups arise

* **Rule-generated (447).** For each document, lexicon-term hits are counted in the file name, the relevance label and up to three rule-selected evidence extracts; the three highest-scoring threat categories are kept as
  `document-keyword-matches-threat` edges, and category totals give the `document-supports-evidence-dimension` edges. No topic, topic weight or threshold is involved. These edges say that threat-category keywords occur in a
  document's title/label/extracts; they are a different relation from the author-reviewed topic–threat associations and neither support nor contradict them. A descriptive cross-tabulation of 20 such edges against the 10 pairs the
  authors did not retain (each document assigned to its highest-weight topic, a single post-hoc convention) is in `validation/rule_edges_in_excluded_pairs.csv`; no rule or edge was changed because of it.
* **Author-reviewed (24).** Taken from the authors' joint decisions on 34 candidate topic–threat pairs (24 retained: 13 Accept + 4 Modify of the 18 originally proposed, 6 Promote, 1 added T01→TH_PRIVACY; 10 not retained: 1 Reject, 4 Leave conceptual, 5 Drop).
  All 24 edges have the same width; topic proportion is not used as edge weight. The relation is named `topic-associated-with-threat` (the earlier implementation's "identifies" was stronger than the authors' wording).
* **Legacy fixed concept links (73).** Threat→layer, threat→signal, threat→intervention and layer/signal→detection→control links, inherited unchanged from the 2026-06 implementation (74 there; the one `LY_DETECTION→LY_DETECTION` self-loop is no longer generated).
  Their definitions and endpoints were checked for equality with the earlier script; they were not reviewed by the authors in this round.

Known counting convention: `linked_document_count` in `graph_redacted/intervention_matrix.csv` is inherited from the earlier script and counts a high-score anchor edge in addition to the keyword-match edge for the same document (for example TH_CYBER shows 44 = 43 + 1). Cite with that caveat.

## Folders

| Folder | Content |
|---|---|
| `decisions/` | The 34 reviewed topic–threat pairs (`…_34.csv/.json`), the 24 retained edges, the 11 topic records, the input-consistency check (33 checks). Each row: decision, DOC_IDs, physical PDF pages, per-anchor source-check status, agreed explanation, limits. Reviewers are identified only by code: Reviewer A and Reviewer B are the two authors who made the decisions; "Author C" appears only where a text refers to a passage or table supplied by another author and is not a reviewer. Decisions, evidence locations and limits are unchanged. |
| `graph_redacted/` | Graph exports with document-node excerpt text removed (`graph_data_redacted.json`, `.graphml`, `graph_nodes_redacted.csv`), `graph_edges.csv`, `intervention_matrix.csv`, two SVG maps |
| `figures/` | `Figure_K11_topic_threat_associations` (PNG/PDF/SVG): the 24 author-reviewed associations only |
| `validation/` | `validation_report.json` (70 checks), `rerun_comparison.json` (2026-10-02 clean rerun; it lists the hashes of the **original, undelivered** files), rule-layer consistency records |
| `code/` | `01`–`07` scripts, path-parametrised copies (`01` also anonymised; see `../CODE_CHANGE_LOG.md`); `requirements.txt` lists the two third-party packages |

## Source-check status of the three hard-to-find PDFs

Three cited documents (D28078c8a10cc, Dfed6d84a0e4f, Db80703b6ee6c) could not be located by the authors; in the decision tables their anchors carry
`table_excerpt_author_not_located` (`source_check_status_per_anchor`) or `table_excerpt_only_author_could_not_locate_pdf` (pair level). A separate **server-side** check
(`06_recheck_three_pdfs.py`, output kept in the internal master as `provenance/three_pdf_server_recheck.json`) found the PDFs on the server, hash- and page-count-identical to the corpus manifest,
with the cited phrases on the cited physical pages. That is a server check, not an author re-review and not a joint independent verification of all sources.

## Running the code

Environment variables replace the former absolute paths:

| Variable | Used by | Points to |
|---|---|---|
| `CHBR_SYNC_ROOT` | `01`,`02`,`03`,`07` | working directory that contains `incoming/Electronic_Supplement_A1/tables/` and `qwen_65docs/preflight/document_evidence_table_65.csv` (`01` also reads the Guide/Checklist markdown and the label workbook, which are internal and not distributed) |
| `CHBR_OLD_REPO_ROOT` | `03` | checkout of the earlier repository version (reads its `code/05_build_free_graph_pack.py` for a compatibility check) |
| `CHBR_PROJECT_ROOT` | `06` | project root that holds the PDF copies used for the three-PDF check |

Interpreter: Python 3.12 (`/apps/python/3.12.0` on the server). Third-party packages: `matplotlib` (`04`; 3.8.0 on the server), `openpyxl` (`01`; 3.1.2). `02`, `03`, `05`, `06`, `07` use the standard library (`06` calls `pdftotext`/`pdfinfo`).
Order: `01` → `02` → `04` → `03` (or `05_rerun_check.py --root <dir>` for all of them in a clean copy).

**Limits for outside readers.** Rebuilding the graph needs `document_evidence_table_65.csv` (contains PDF excerpts; produced by the Qwen step 2 from the lawfully obtained PDFs) and, for `01`, the internal review guide files.
Without them, readers can inspect, query and re-validate the shared exports and decision tables but cannot regenerate the graph.

**Checks made on the server (existing files read; outputs written to a scratch directory only).**
* *Deterministic rebuild of the original pipeline:* with path-parametrised copies of the original code (before anonymisation) and the environment variables set, steps 01, 02, 04, 03 were re-run in a clean directory; the 18 files of `decisions/` (5), `graph_pack/` (10) and `figures/` (3) were byte-identical to the 2026-10-02 outputs of the same pipeline, the validation report was identical and all 70 checks passed. Step 07 outputs were also identical.
* *Delivered copies:* the files in this folder are anonymised or de-excerpted derivatives with their own hashes (`../SNAPSHOT_LEDGER.csv`); they are not byte-identical to those originals. The delivered decision files were confirmed to equal the documented anonymisation of the rebuilt originals; the delivered code differs from the parametrised originals only in one anonymised provenance line.
These checks confirm deterministic reconstruction of the recorded files. They do not validate the topic model, the author mappings or the rule-generated edges scientifically.
