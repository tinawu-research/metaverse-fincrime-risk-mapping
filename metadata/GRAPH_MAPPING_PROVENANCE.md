# Graph Mapping Provenance

Prepared: 2026-06-25

## Purpose

This note clarifies how the graph edges should be interpreted. It is important not to present all graph edges as if they were direct LDA results or manually verified evidence claims.

## Edge Types In `graph_edges.csv`

Observed relation counts:

| Relation | Count | Provenance classification |
|---|---:|---|
| `document-supports-evidence-dimension` | 225 | Rule-generated from keyword/evidence counts |
| `document-indicates-threat` | 175 | Rule-generated from keyword matches in titles/evidence excerpts |
| `high-evidence-anchor` | 3 | Rule/scoring-generated high-evidence flag |
| `topic-identifies-emerging-threat` | 21 | Interpretive topic-to-threat mapping for author review |
| `threat-operates-through-layer` | 9 | Interpretive conceptual mapping for author review |
| `modelled-by-signal` | 9 | Interpretive conceptual mapping for author review |
| `analytical-signal` | 9 | Interpretive conceptual mapping for author review |
| `intervention-point` | 27 | Interpretive threat-to-intervention mapping for author review |
| `converted-into-control` | 13 | Interpretive control/intervention mapping for author review |
| `feeds-detection-and-intervention` | 7 | Interpretive framework mapping for author review |

An audit-friendly file has also been prepared:

- `graph_edges_with_provenance.csv`

This file is derived from `graph_edges.csv` and adds `provenance_category`, `provenance_note`, and `submission_caution` columns to every edge.

## How To Describe The Graph

Suggested wording:

The graph was used as an analytical and explanatory layer rather than as an independent statistical model. Document-to-evidence and document-to-threat edges were generated through transparent rule-based keyword matching applied to document titles and extracted evidence snippets. Topic-to-threat, threat-to-signal, and threat-to-intervention edges were interpretive conceptual mappings derived from the Round 5 topic labels, topic prevalence outputs, and the author's synthesis of the literature. These conceptual mappings should be reviewed by the author team before final submission and should not be described as direct LDA outputs.

## Practical Interpretation

- Rule-generated document edges are reproducible from the CSV/JSON evidence tables and keyword rules.
- Topic-to-threat mappings translate topic-model labels into threat environments; they are a conceptual interpretation of the model, not a separate statistical result.
- Intervention mappings translate threat environments into analytical signals and possible control points; they are authorial synthesis and should be labelled as such.
- The graph can support explanation and auditability, but manuscript claims should still be tied back to the topic-model outputs and the underlying literature.
