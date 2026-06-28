# Metaverse-Cryptocurrency Financial Crime Reproducibility Package

This repository is a reviewer-facing reproducibility package for the paper provisionally titled **Mapping Financial Crime Risks in the Metaverse-Cryptocurrency Ecosystems: A Topic-Modelling and Local LLM-Assisted Evidence Synthesis**.

It contains code, metadata, provenance notes, selected aggregate outputs, redacted derived tables, and figures for auditing the computational workflow. It is prepared as a candidate GitHub package for author review and is not itself a final published repository.

## What This Package Contains

- LDA/topic-modelling notebook and local Qwen/Ollama workflow scripts in `code/`.
- Run metadata, graph provenance, and workflow manifests in `metadata/`.
- Safe aggregate LDA outputs in `outputs/lda/`.
- Redacted Qwen evidence summaries in `outputs/qwen/`.
- Graph edge tables, provenance tables, redacted graph data, and graph matrices in `outputs/graph/`.
- LDA and graph figures in `figures/`.
- Reproducibility notes and exclusion rationale in `docs/`.

## What This Package Does Not Contain

This package does not redistribute full-text PDFs, full extracted corpus text, or Qwen batch/report files that contain long verbatim excerpts from source publications. Those files are excluded because they may contain copyrighted publisher material.

Users who want to fully rerun PDF extraction must lawfully obtain the source PDFs themselves and place them in the expected input folder described in `REPRODUCING.md`.

## Workflow Overview

The study used a PRISMA-informed corpus construction process to identify a final corpus of 59 full-text documents. The corpus was processed in Python and modelled with Latent Dirichlet Allocation (LDA). Candidate topic counts from K=3 to K=8 were evaluated with coherence and model diagnostics, and a seven-topic solution was retained.

After topic modelling, a locally hosted Qwen 2.5 model through Ollama was used as an interpretive aid to organise extracted evidence into evidence dimensions, threat environments, analytical signals, and intervention points. The graph/intervention framework was then built locally from topic-model outputs and derived evidence tables. Document-to-evidence and document-to-threat graph edges are rule-generated; topic-to-threat and threat-to-intervention mappings are interpretive conceptual mappings for author review.

## Repository Layout

- `code/` - LDA notebook and local Qwen/graph-building scripts.
- `outputs/lda/` - CSV exports of safe aggregate topic-model outputs.
- `outputs/qwen/` - redacted document-level evidence counts and aggregate Qwen manifest values.
- `outputs/graph/` - graph edge/provenance tables, intervention matrix, and redacted graph JSON.
- `metadata/` - run metadata, graph provenance, manifests, and model notes.
- `figures/` - generated LDA and graph figures that do not contain full-text corpus material.
- `docs/` - excluded-file list, full code listing, and notes for reviewers.

## Citation

Please see `CITATION.cff` for a draft citation record. Final DOI, journal, and publication details have not yet been assigned.

## License Status

No open-source license has been selected yet. See `LICENSE_NOTICE.md` before public redistribution.
