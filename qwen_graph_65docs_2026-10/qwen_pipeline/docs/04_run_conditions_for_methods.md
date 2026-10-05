> **Delivery copy (2026-10-05).** Sanitised from the 2026-09-29 draft: scheduler/account/host identifiers, personal machine details and author names (replaced by reviewer codes) removed; no other change. References to project-relative paths (`qwen_65docs/...`, `internal_reviewer_snapshot_20260929/...`) name files of the project working directory, not files of this delivery; the delivered counterparts are listed in the attachment manifest.

# Run Conditions — Ready-to-Adapt Notes for Methods/Supplement

Source of record: `qwen_65docs/qwen/STAGE2_completion_20260922.md` (full audit,
not repeated here). This file distils those facts into Methods-ready form and
records one correction. The manuscript itself was not edited. Updated
2026-09-22 (third pass) to separate manuscript-facing wording from
operational/supplement detail and to remove stale pending-decision items.

## Proposed Methods wording — Qwen input pipeline

Labelled **proposed**; not yet reviewed or approved by the authors, and no
claim here should be read as "author-verified."

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

Any manuscript or supplement text describing this synthesis should keep this
wording's framing — a two-stage, excerpt-based analysis rather than a
full-text review — and note that DOC_ID-level claims quoted from it should be
checked against `qwen_65docs/review/02_synthesis_traceability.md` before being
cited as corpus findings.

## Proposed Methods wording — model and configuration

Also labelled **proposed**, and kept manuscript-scale (model identity,
version, and generation settings only — scheduler/account/hardware detail is
in the operational record below, not here):

> The synthesis used `qwen2.5:7b` (`Q4_K_M` quantisation) served locally via
> Ollama 0.34.2, with `temperature=0.2`, `top_p=0.9`, `num_ctx=32768`,
> `num_predict=1800` per batch (`4200` for the final synthesis), batch size 5
> (13 batches covering all 65 documents exactly once), and `seed=42`. The
> seed is a prospective setting recorded for this run; it is not a
> reconstruction of a seed used in any earlier run, and the historical run's
> Ollama version, hardware, and seed are not recorded anywhere in the project
> materials available to this review — a documentation gap, not something
> that blocks reviewing the current run. The historical (59-document) and
> current (65-document) Qwen outputs are separate runs on different corpus
> versions, not a reproduction of one another and not statistically
> independent samples of anything — "separate," not "independent," is the
> accurate description. All 13 batch outputs cite exactly the 5 DOC_IDs in
> their own batch and no others; the final synthesis cites none (also true of
> the historical run).

## Internal operational record (not manuscript prose)

Scheduler, account, and hardware identifiers, and the home-directory side
effect, are recorded here for the internal record / reproducibility
supplement — they should not appear in the manuscript's Methods paragraph
itself:

- an HPC batch job (scheduler, partition, node and account identifiers withheld),
  1×NVIDIA H100, executed 2026-09-22.
- Model identity (id `845dbda0ea48`, layer/config digests) confirmed against
  the project handover record before generation ran — see
  `STAGE2_completion_20260922.md` §2 for the full comparison.
- The home-directory registry-keypair side effect
  (the Ollama key-pair files in the user's home directory) — see "Scope-statement correction" below,
  which is itself an internal-record correction, not manuscript text.

## Facts authors still need to supply/decide

1. Ollama version, hardware, and seed for the **historical** 59-document run
   are not recorded anywhere available to this review. This is a
   documentation limitation for the eventual Methods/supplement text, not a
   blocker to reviewing or using the current (65-document) run.
2. `qwen_65docs/README.md` describing the current run's provenance and its
   relationship to the preserved historical outputs — deferred, not urgent.
   This is a labelling/provenance note, not a comparative analysis.

**Corrected 2026-09-28 (superseding `STAGE2_completion_20260922.md` §7 item 3,
which listed "how the two result sets should be presented side-by-side" as
an open author decision — that framing is now outdated).** The revision
**uses the 65-document Qwen results**; the 59-document outputs are
**retained as a historical record only**, and **no side-by-side comparison
analysis between the two is currently planned.** This is not a new decision
made by this review — it reflects what the user has now confirmed — but it
does correct the earlier "deferred/TBD" framing carried in this file and in
`STAGE2_completion_20260922.md` (the latter is an original Stage ②
completion report and is not edited here; this note supersedes its §7 item 3
for anyone reading this file going forward).

## Current status and next steps (updated 2026-09-22, third pass)

**No Qwen rerun is currently planned** — including no rerun with a
citation-requiring prompt. If the authors later want one, that is a new,
separate decision; nothing here is waiting on it.

The remaining work is two **separate** tracks; the Qwen synthesis should not
be judged against, or blocked on, K=11/LDA material — the two pipelines took
different inputs (see the Methods wording above) and the LDA labels were
never an input to Qwen:

1. **Editorial-draft review**: authors review
   `05_synthesis_editorial_draft.md` against its cited source evidence
   (`02_synthesis_traceability.md`) and decide what, if anything, to carry
   into the manuscript.
2. **Stage ③ graph preparation** (unrelated to track 1): verification of the
   current, Drive-aligned K=11 topic labels, and author confirmation of the
   topic→threat mapping — see `03_topic_threat_mapping.md`. This track's
   status is unchanged by anything in this file.

## Scope-statement correction

*(Internal operational record — corrects `STAGE2_completion_20260922.md`'s
own wording; not manuscript prose.)*

`STAGE2_completion_20260922.md` §6 currently reads (translated): *"Writes were
limited to `qwen_65docs/qwen/` and `qwen_65docs/ollama_runtime/`... none of
[other locations] were changed,"* with a **separate** bullet two lines later
disclosing: *"One side effect within the account: on first launch, `ollama
serve` generated a registry keypair (key-pair files) under `~/.ollama/` (468
bytes total, standard Ollama behaviour, nothing uploaded). Not deleted."*

Strictly read, the first "writes were limited to..." sentence is incomplete —
`~/.ollama/` is the account **home directory**, outside both named
`qwen_65docs/` paths. The keypair is a real, current side effect, independently
confirmed for this review:

```
-rw------- 1 <user> <group> 387 Sep 22 19:45 <Ollama key file in the user's home directory>       (private key, mode 600)
-rw-r--r-- 1 <user> <group>  81 Sep 22 19:45 <Ollama key file in the user's home directory>   (public key, mode 644)
```

Both timestamped to the job's start time (19:45), consistent with first-launch
key generation as already described. **This review only confirmed presence,
size, permissions, and timestamp via `ls -la` — the key contents were not
read, copied, or packaged, per instructions.**

**Recommended correction** (for whoever next edits `STAGE2_completion_20260922.md`
or writes the internal reproducibility record — not applied here): fold the
keypair fact into the scope sentence itself, e.g. *"Writes were limited to
`qwen_65docs/qwen/`, `qwen_65docs/ollama_runtime/`, and one home-directory
side effect (the Ollama key-pair files in the user's home directory, a standard Ollama first-run
registry keypair, retained and not uploaded anywhere)"* — rather than stating
an unqualified two-directory boundary and disclosing the exception separately.
This is a documentation-accuracy correction only; no file write behaviour
changed.
