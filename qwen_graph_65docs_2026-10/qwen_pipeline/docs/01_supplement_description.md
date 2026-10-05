> **Delivery copy (2026-10-05).** Sanitised from the 2026-09-29 draft: scheduler/account/host identifiers, personal machine details and author names (replaced by reviewer codes) removed; no other change. References to project-relative paths (`qwen_65docs/...`, `internal_reviewer_snapshot_20260929/...`) name files of the project working directory, not files of this delivery; the delivered counterparts are listed in the attachment manifest.

# Supplement Description — Qwen/Ollama-Assisted Synthesis of the 65-Document Corpus

**Status: draft for author review, not yet approved or submitted.**

## 1. What this pipeline is

This supplement documents a second, independent analysis pipeline applied to
the same 65-document corpus used for the LDA topic modelling in
`Electronic_Supplement_A1`: a locally hosted large language model
(`qwen2.5:7b`, served via Ollama) that reads a **rule-derived digest** of
each document — not the document itself — and produces first a set of
batch-level summaries, then one final synthesis. It was run once, on
2026-09-22 (an HPC batch job), and has not been rerun since. No cloud or
paid API was used at any point.

## 2. What Qwen did and did not receive

**Qwen never received the LDA topic-model output**, and **it never received
full document text or full PDF pages.** Its only input, at every stage, was
produced by a fixed, deterministic, rule-based procedure (Task 3 of this
package, `03_deterministic_rules_and_code.md`) applied to per-document
extracted text. Concretely, in two stages:

- **Stage A — 13 batch calls (5 documents each).** For each document, a
  fixed-shape digest containing: `doc_id`, `filename`, page/word counts, a
  2-way relevance tier, keyword-category hit counts (4 categories), the top
  5 terms per category, and up to 5 rule-selected text excerpts (roughly
  80–350 characters each; some are full sentences, some are non-sentential
  table/caption fragments carried over from PDF extraction). Batch size was
  5 documents, 13 batches, covering all 65 documents exactly once.
- **Stage B — 1 final-synthesis call.** The model's own 13 batch outputs
  (i.e., Qwen synthesizing its own prior generations), corpus-wide aggregate
  keyword/relevance statistics (sums only, not per-document detail), and
  metadata (doc_id/filename/relevance/category totals — **no excerpt text**)
  for the 20 documents with the highest rule-based evidence score.

This means the final synthesis is **two inferential steps removed** from the
source PDFs: PDF text → rule-based excerpt/count extraction → batch-level
Qwen synthesis → final Qwen synthesis over the batch summaries. Any claim in
the model's output that cannot be traced back, through a batch output, to a
specific rule-selected excerpt should be treated as the model's own
elaboration on the research question, not as a corpus-derived finding —
`qwen_65docs/review/02_synthesis_traceability.md` performs exactly this
trace for every claim that is a candidate for use in the manuscript.

**Do not describe this pipeline, in the manuscript or anywhere else, as
Qwen having "read" the 65 documents.** It read short, rule-selected excerpts
and counts, twice removed by the final-synthesis stage.

## 3. Proposed Methods-paragraph wording

The following wording (from `qwen_65docs/review/04_run_conditions_for_methods.md`,
labelled there as **proposed, not yet author-approved**) is repeated here as
the anchor text for this supplement's own framing:

> Both the LDA analysis and the Qwen-assisted synthesis used the same
> 65-document corpus, but Qwen did not receive LDA outputs. A fixed
> rule-based procedure constructed a digest for each document containing its
> filename, page and word counts, relevance tier, keyword-category counts,
> the five highest-frequency terms per category, and up to five selected text
> excerpts. The digests were processed in 13 batches of five documents using
> `qwen2.5:7b`. A final synthesis call received the 13 batch summaries,
> corpus-level keyword and relevance statistics, and metadata for the 20
> highest-scoring documents; it did not receive the source excerpts. Full
> document texts were not supplied to Qwen at either stage. The synthesis
> therefore reflects selected excerpts and sequential summarisation rather
> than direct model analysis of the complete document texts.

## 4. Two batches of 13+1 requests, exactly once each

13 batch calls + 1 final-synthesis call = 14 total generations. Every one
completed with Ollama's `done_reason="stop"` (normal completion, no
truncation) and required zero retries. Full per-call byte sizes, sha256
digests, and token counts are in `02_request_response_index.csv`; which 5
`doc_id`s went into each of the 13 batches is in
`02_batch_document_mapping.csv`. Full prompt text (verbatim) and every
configuration value are in `02_prompts_and_configuration.md`.

## 5. Relationship to the historical 59-document run

The 59-document Qwen run is a **separate, earlier generation on a different
corpus version** — not a reproduction of this run and not a statistically
independent sample of anything. Its own Ollama version, hardware, and seed
are not recorded anywhere available to this review (a documentation gap,
not a blocker). The revision **uses the 65-document results**; the
59-document outputs are retained as historical record only, and no
side-by-side comparison between the two is currently planned. See
`qwen_65docs/review/04_run_conditions_for_methods.md` for the full
correction record on this point.

## 6. Known limitations to disclose alongside this pipeline

- `final_synthesis.md` contains **zero DOC_ID citations** anywhere in its
  original form (also true of the historical 59-document run) — the
  editorial draft (`04_outputs_and_verification.md` §2) adds citations only
  where a specific document-level source was independently traced.
- Several subsections of the original synthesis (Indicators and Red Flags,
  Cross-Border Cooperation, Law Enforcement, Data
  Collection/Preprocessing/Feature Engineering) were checked against **all
  three** of Qwen's actual synthesis inputs and found to have **no basis in
  any of them** — they read as the model's own generic domain knowledge.
  These are removed, not merely hedged, in the editorial draft.
- One synthesis claim ("high energy consumption of NFTs can be used to
  obscure financial transactions") is a confirmed **fabricated conflation**
  of two unrelated bullets from the same batch — removed from the editorial
  draft.
- This is a **preliminary, excerpt-based text-mining/summarisation
  component**, not a systematic review finding and not a claim of
  independent corroboration across documents (recurrence of a phrase across
  batches reflects a shared prompt template applied 13 times, not 13
  independent confirmations).

Full detail and the targeted claim-traceability and source checks are in
`04_outputs_and_verification.md`.
