> **Delivery copy (2026-10-05).** Sanitised from the 2026-09-29 draft: scheduler/account/host identifiers, personal machine details and author names (replaced by reviewer codes) removed; no other change. References to project-relative paths (`qwen_65docs/...`, `internal_reviewer_snapshot_20260929/...`) name files of the project working directory, not files of this delivery; the delivered counterparts are listed in the attachment manifest.

# Prompts, Templates, and Run Configuration — Qwen/Ollama Pipeline

**Status: draft for author review.** Every template and value below is
transcribed verbatim from files already saved on disk before this round
began (`qwen_65docs/qwen/requests/*.json`, `qwen_65docs/qwen/run_record.json`,
`qwen_65docs/qwen/model_check.json`, `qwen_65docs/qwen/job_record.json`,
`qwen_65docs/ollama_runtime/logs/ollama_serve_32828822.log`,
`qwen_65docs/ollama_runtime/logs/chbr_qwen65_stage2_32828822.out`,
`qwen_65docs/ollama_runtime/stage2_qwen65.sbatch`, and the code in
`code_copies/`). Nothing here was reconstructed or re-derived by asking a
model to reproduce a template, and nothing about server-side implementation
is inferred from the endpoint path, response fields, or the model tag alone
— every claim below is a direct read of a saved log or record, or of the
code that actually ran. No service was queried or started to prepare this
section; Ollama is not installed on the login node used for this work.

**Revised 2026-09-29: §1 corrected and expanded** after a discrepancy was
flagged between this file's earlier "Endpoint" row (which read
`http://localhost:11434/api/generate`, copied from the analysis script's
hardcoded default constant) and the actual, saved completion record, which
uses a different, dynamically assigned loopback port. The correction below
traces this to ground truth across every independent saved record that
mentions an endpoint, rather than picking one account and discarding the
other, because — as shown below — this is not actually a contradiction
between two records of the same fact; it is two different facts (an unused
source-code default vs. the runtime override actually used), and this file
had previously reported the wrong one of the two as if it were what ran.

## 1. Confirmed execution path, actual endpoint/backend, and what the request record does and does not establish about a "system prompt"

### 1(a). The actual endpoint used for all 14 calls, and why it differs from the script's default constant

**All 14 requests were sent to `http://127.0.0.1:42471/api/generate`** — a
loopback port dynamically assigned by the operating system for this one
Slurm job, **not** the value `http://localhost:11434/api/generate` hardcoded
as the `OLLAMA_URL` constant in
`code_copies/01_local_qwen_metaverse_fincrime_analysis.py` line 21. This is
confirmed, in agreement, across eight independently written, already-saved
records:

| Record | What it shows |
|---|---|
| `qwen_65docs/qwen/run_record.json` | `"endpoint": "http://127.0.0.1:42471/api/generate"` |
| `qwen_65docs/qwen/job_record.json` | `"endpoint": "loopback 127.0.0.1:<random free port chosen inside the job>; never exposed on the network"` |
| `qwen_65docs/qwen/run_log.jsonl` | Both `run_start` events: `"endpoint": "http://127.0.0.1:42471/api/generate"` |
| `qwen_65docs/qwen/model_check.json` | `"endpoint_base": "http://127.0.0.1:42471"` |
| `qwen_65docs/ollama_runtime/logs/model_identity_check_32828822.json` | `"base": "http://127.0.0.1:42471"` |
| `qwen_65docs/ollama_runtime/logs/chbr_qwen65_stage2_32828822.out` (job stdout) | `"loopback endpoint: http://127.0.0.1:42471 | ... | binary: .../ollama_runtime/install/bin/ollama"` |
| `qwen_65docs/ollama_runtime/logs/ollama_serve_32828822.log` (Ollama's own startup log) | Env dump: `OLLAMA_HOST:http://127.0.0.1:42471`; then `msg="Listening on 127.0.0.1:42471 (version 0.34.2)"` |
| `qwen_65docs/ollama_runtime/stage2_qwen65.sbatch` (the launch script) | Lines 38–43: binds a Python socket to `127.0.0.1:0` to obtain an OS-assigned free port, `export OLLAMA_HOST=127.0.0.1:$PORT`, then passes `--endpoint $BASE/api/generate` explicitly to `run_stage2_qwen.py` |

**The `11434` value is real but is the unused source-code default, not what
this run contacted.** It appears in the imported analysis script's
`OLLAMA_URL` constant and in a pre-run planning document,
`qwen_65docs/qwen/STAGE2_status_20260922.md` (written before the job ran) —
that same planning document explicitly records that port 11434 on the
login node was, at the time, already occupied by an unrelated Ollama
instance under a different account, which is exactly why the actual job's
launch script (above) deliberately obtains a fresh, dynamically assigned
port instead of using the default. **This is not a conflict between two
records of the same run** — it is a source-code default that the launch
script explicitly overrides via the `--endpoint` argument, evidenced
end-to-end from the port-selection line in the sbatch script through to
Ollama's own startup log and every run-record file above.

**Correction to code attribution:** the HTTP call itself, for this run, was
made by `run_stage2_qwen.py`'s own `generate(base_url, payload, log_path,
label)` function (source-commented as *"Mirror of ollama_generate() (script
lines 175–203) with full-response capture and per-attempt logging"*), using
`base_url` = the `--endpoint` value above — **not** by
`ollama_generate()` in `01_local_qwen_metaverse_fincrime_analysis.py`, which
is only used by this run for its prompt-building functions
(`build_batch_prompt`/`build_final_prompt`/`make_doc_digest`), not for
sending requests. `run_stage2_qwen.py` defines its own `RETRIES = 2` and
`TIMEOUT_S = 900` constants independently (lines 52–53) — the same values
as `ollama_generate()`'s defaults, but not imported from it. This corrects
this file's earlier §5 sourcing, which attributed the retry/timeout
behaviour to the wrong function; the values themselves were already
correct.

### 1(b). Actual launched executable, its recorded version, and the Ollama↔llama-server relationship

Strictly from `qwen_65docs/ollama_runtime/logs/ollama_serve_32828822.log`
(Ollama's own log of this run, not re-queried) and
`qwen_65docs/qwen/job_record.json`:

- **The process that received all 14 requests is the `ollama` binary
  itself** (`ollama_runtime/install/bin/ollama`, per `job_record.json`),
  version **0.34.2**, self-reported at startup: `msg="Listening on
  127.0.0.1:42471 (version 0.34.2)"`.
- **This Ollama process itself spawns a second, child process** to perform
  inference. The log records this directly: at 19:45:16.933,
  `source=server.go:100 msg="using llama-server for model"`, immediately
  followed (19:45:16.948, `source=llama_server.go:434`) by the exact
  spawned command line: `.../ollama_runtime/install/lib/ollama/llama-server
  --model <blob path> --port 40891 --host 127.0.0.1 --no-webui --offline -c
  32768 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps
  --no-jinja --chat-template chatml --flash-attn auto -b 1024 -ub 1024
  --context-shift --keep 4`. The `-c 32768 -np 1 --flash-attn auto
  --chat-template chatml` flags quoted in §5 below are a direct, verbatim
  read of this logged command line, not a restatement or inference.
- **This `llama-server` binary ships inside the same Ollama install
  directory** (`install/lib/ollama/llama-server`) — it is Ollama's own
  bundled copy, not a separately installed or independently versioned piece
  of software. Its own log line records its build identity directly:
  `common_params_print_info: build 1 (391fac164) with GNU 13.3.1 for Linux
  x86_64`.
- **This child process listens on a second, different, internal-only
  loopback port, 40891** (`srv llama_server: listening on
  http://127.0.0.1:40891`, model loaded 28.58 s after being started). **No
  saved request in this package, and no code in this pipeline, ever
  contacts this port directly** — every one of the 14 requests went only to
  Ollama's own port, 42471.
- **Relationship, and whether a separate adapter layer exists:** Ollama
  0.34.2 is the outer daemon implementing the Ollama HTTP API
  (`/api/generate`, `/api/show`, `/api/tags`, `/api/version` — all four of
  which this pipeline's own code or its identity check used) and the
  Modelfile/template handling described in §1(c) below; it internally
  manages the `llama-server` child process (its own bundled llama.cpp-based
  inference server) and forwards requests to it. **This is Ollama's own
  documented internal architecture, directly evidenced by its own log
  output for this specific run — there is no separate, third-party
  "Ollama-API-compatible" adapter layer in front of a different backend.**
  No record anywhere in this project shows any other software receiving or
  handling these 14 requests.
- **Execution path for each of the 14 calls, reconstructed only from the
  records above:** `run_stage2_qwen.py`'s `generate()` → HTTP POST to
  `http://127.0.0.1:42471/api/generate` (the Ollama daemon) → Ollama applies
  its own Modelfile/template handling (§1(c)) → Ollama forwards the request
  to its already-running `llama-server` child process on the internal port
  40891 → `llama-server` performs the CUDA inference on the allocated H100
  → the response is returned by Ollama to the caller and saved verbatim to
  `qwen_65docs/qwen/responses/*_response.json`.

### 1(c). What the request record shows, and does not establish, about a "system prompt"

**Because §1(a)–(b) above directly confirm the actual backend for this run
is Ollama 0.34.2 with its own bundled `llama-server` — not an unconfirmed
or different backend — it is legitimate to reason about Ollama's own
documented request-handling default for this specific run. This reasoning
is not being applied to any other, unconfirmed backend.**

**Two separate facts, kept separate:**

**No application-set `system` field is present in any saved request.**
Every one of the 14 saved request JSONs has exactly four top-level keys —
`model`, `prompt`, `stream`, `options` — confirmed by direct inspection of
all 14 files. There is no `system`, `messages`, or `role` key anywhere in
any of them. The "you are analysing a corpus for an academic study..."
framing (§2 below) is part of the single `prompt` string the driver script
builds — it was never passed as a separate system-role field by this
pipeline's own code.

**This does not establish that no system prompt was in effect at inference
time — the request record is silent on that, and this round does not fill
that silence by assumption.** `qwen_65docs/qwen/model_check.json` (produced
by a live `/api/show` call made *during this same run*, at
`http://127.0.0.1:42471` — see `model_identity_check()` in
`code_copies/run_stage2_qwen.py` — not re-queried by this review after the
fact) records two directly relevant facts about the `qwen2.5:7b` model as
actually served for this run. The full, saved values are reproduced
verbatim, not just excerpted, in
`internal_reviewer_snapshot_20260929/verification/model_check_show_template_and_modelfile.txt`
(added this round — see §1(d) below):

- `show_modelfile` contains the line `SYSTEM You are Qwen, created by
  Alibaba Cloud. You are a helpful assistant.` — a **default system string
  baked into the model's own Ollama Modelfile**, not authored by this
  study's pipeline or its prompt-building code.
- `show_template` is Qwen's ChatML template, which — for a `/api/generate`
  call with no `.Messages` (i.e. this pipeline's raw single-prompt calls) —
  renders `{{- if .System }}<|im_start|>system\n{{ .System }}<|im_end|>\n{{ end }}`
  **before** the user-turn content, i.e. it inserts a system block whenever
  a `System` value is present at render time. §1(b) above directly confirms
  the running `llama-server` was launched with `--chat-template chatml`,
  consistent with this template actually being the one in effect for this
  run (not inferred from the endpoint path or model tag alone — read
  directly from the logged launch command).
- None of the 14 saved requests sets `"raw": true` (which would bypass
  templating entirely) or overrides `"system"` in the request body.

**Ollama's documented default behaviour is that when a request omits
`system` and does not set `raw: true`, the model's own Modelfile `SYSTEM`
string fills that template slot.** Based on that documented behaviour, the
now-confirmed execution path in §1(a)–(b), and the two facts above, **the
most accurate statement this review can make is: no system field was set by
this pipeline's own code, but the model's own default system string was
very likely in effect at inference time via Ollama's standard (non-raw)
template rendering — this was not suppressed by anything in the saved
requests.** This round did **not** capture the raw, post-template-rendered
text actually sent from the Ollama daemon (port 42471) to the internal
`llama-server` process (port 40891) for any of the 14 calls, so it cannot
independently confirm byte-for-byte that this default string was inserted
for this specific run; **no record in this project directly proves the
actual rendered input** — that is the one gap between "documented default
behaviour, on a now-confirmed backend, not overridden here" and "directly
observed for this run." **Do not report a "no system prompt was used"
conclusion from this pipeline** — the correct statement is the two-part one
above, not its first half alone.

**If the manuscript or supplement needs a single "system prompt" entry for
a table:** "Not set by the analysis pipeline's own request; the underlying
Ollama-served `qwen2.5:7b` model's own default Modelfile system string
(`You are Qwen, created by Alibaba Cloud. You are a helpful assistant.`)
was not overridden or suppressed and was the model's standard default at
the time of this run (Ollama 0.34.2, confirmed backend — §1(a)–(b)); the
actual post-template-rendered input was not captured and cannot be
confirmed byte-for-byte" — not "none" and not a fabricated
pipeline-authored system prompt.

### 1(d). Full, unexcerpted configuration record now in the snapshot

**Revised 2026-09-29: corrected wording below — the two files in this
section have different kinds of verification, not the same one.**

Two related but distinct files are in
`internal_reviewer_snapshot_20260929/verification/`, both sourced from
`qwen_65docs/qwen/model_check.json`:

- **`model_check.json`** — a verbatim, unedited copy of the source file.
  This one **is** sha256-identical to its source
  (`internal_reviewer_snapshot_20260929/00_SOURCE_HASH_LEDGER.csv` records
  matching sha256 for both, `identical: True`) — a whole-file byte-identity
  check, the strongest verification this package makes for any copied file.
- **`model_check_show_template_and_modelfile.txt`** — a **derived, reformatted
  plain-text extract** of specific field values from that same JSON
  (`show_template`, `show_modelfile` — including its `SYSTEM` line and its
  embedded Apache License text, reproduced in full rather than trimmed —
  plus `show_parameters`, `show_details`, and `show_model_info_subset`).
  **This file cannot be, and is not claimed to be, sha256-identical to the
  whole source JSON** — reformatting (adding section headers, converting
  from a JSON string value to plain text) necessarily changes the file's
  bytes even though no field content was altered. What **is** verified for
  this file, and recorded as such in the hash ledger (`identical:
  N/A_derived_not_identity_copy`, with a note explaining why): each of the
  `show_template` and `show_modelfile` field values from the source JSON
  was confirmed, this round, to appear as an **exact, complete substring**
  of this text file — i.e. content-level fidelity of those specific fields
  (nothing truncated, altered, or paraphrased), not file-level byte
  identity. Anyone who wants the whole-file byte guarantee should use
  `model_check.json` directly, which is included for exactly this reason.

§1(c) above quotes the operative lines from these fields; the full record
is in these two files for anyone who wants to check nothing was left out of
that quotation.

## 2. Batch prompt template (used 13 times, one per batch)

Verbatim from `build_batch_prompt()` in
`code_copies/01_local_qwen_metaverse_fincrime_analysis.py` (lines 227–247),
confirmed to match the actual text inside every saved
`qwen_batch_NN_request.json`:

```
You are analysing a corpus for an academic study. Use only the supplied document evidence.

Research question:
{QUESTION}

Batch {batch_index} of {batch_count}. For each document, identify what it contributes to the question.
Then synthesize cross-document insights for this batch.

Return concise but specific markdown with these headings:
1. Document-level findings with DOC_ID references
2. Financial-crime opportunity mechanisms
3. Modelling/analysis signals
4. Intervention points
5. Gaps or limits in this batch

Document evidence:
{docs_text}
```

Where `{docs_text}` is 5 per-document digests (see §4 below), joined by a
`---` separator line, and `{batch_index}`/`{batch_count}` range 1–13/13.

## 3. Final-synthesis prompt template (used once)

Verbatim from `build_final_prompt()` (lines 250–285):

```
You are writing the final synthesis for an academic research analysis.

Research question:
{QUESTION}

Method boundary: The corpus was analysed locally with qwen2.5:7b through Ollama. Do not imply any cloud or paid API use.
Use only the batch summaries and aggregate evidence supplied below. Cite DOC_IDs where useful.

Aggregate corpus statistics:
{aggregate_stats as indented JSON}

Most relevant documents by evidence score:
{top_doc_text}

Batch summaries:
{batch_summaries}

Write a complete, structured analytical report in English with these sections:
- Executive answer
- Mechanism model: how metaverse and crypto features combine
- Financial crime typology matrix
- Modelling and analytical framework
- Intervention points across the lifecycle
- Indicators and red flags
- Implications for AML/CTF, regulation, platforms, exchanges, and law enforcement
- Research gaps and limitations
- Conclusion

Keep the tone academic and precise. Do not invent facts outside the supplied evidence.
```

`{top_doc_text}` lists the top 20 documents by `evidence_score`
(`TOP_DOCS_FOR_FINAL = 20`, set in `run_stage2_qwen.py`) as one line each:
`doc_id: filename | relevance tier | category_totals`. **No excerpt text is
included at this stage** — only the metadata line above. `{batch_summaries}`
is the literal concatenation of the model's own 13 batch outputs
(`qwen_65docs/qwen/qwen_batch_summaries.md`).

Note the prompt's own instruction says "Cite DOC_IDs where useful" — the
actual output (`final_synthesis.md`) contains **zero** DOC_ID citations
despite this instruction; this is recorded as-is (see
`04_outputs_and_verification.md`), not corrected or re-requested.

## 4. Per-document digest template (`make_doc_digest()`, lines 206–224)

Each of the 65 documents is rendered into this fixed shape before being
placed into a batch prompt:

```
{doc_id} | {filename}
Pages: {pages} | extracted words: {extracted_words} | relevance: {relevance}
Category totals: {category_totals as JSON}
Top terms: {category}: {term}={count}, ... (up to 5 terms/category, across 4 categories)
- Evidence 1: {snippet text}
- Evidence 2: {snippet text}
... up to 5 (item["snippets"][:5] — the rule pipeline stores up to 7 per document, but only the first 5 by score are ever placed into a prompt)
```

The Research question (`QUESTION`, used verbatim, unedited, in both
templates above):

> How do the combined features of metaverse platforms and cryptocurrency
> ecosystems generate new money laundering and other financial crime
> opportunities, and subsequently help model, analyse, and identify
> intervention points within these emerging financial crime environments?

## 5. Model and run configuration

| Field | Value | Source |
|---|---|---|
| Model | `qwen2.5:7b`, `Q4_K_M` quantisation, 7,615,616,512 parameters | `model_check.json` |
| Server (outer daemon, received all 14 requests) | Ollama **0.34.2** (`ollama_runtime/install/bin/ollama`) | `ollama_serve_32828822.log` ("Listening on 127.0.0.1:42471 (version 0.34.2)"); `job_record.json` |
| Inference child process (spawned by Ollama, never itself contacted directly) | `llama-server`, bundled inside the Ollama install (`install/lib/ollama/llama-server`), build `1 (391fac164)`, launched with `--model <blob> --port 40891 --host 127.0.0.1 --no-webui --offline -c 32768 -np 1 --log-verbosity 4 --no-log-prefix --no-log-timestamps --no-jinja --chat-template chatml --flash-attn auto -b 1024 -ub 1024 --context-shift --keep 4` | `ollama_serve_32828822.log` (exact logged launch command) — see §1(b) |
| Ollama model ID | `845dbda0ea48` | `model_check.json` |
| Model-layer digest | `sha256:2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730` | `model_check.json` |
| Config-layer digest | `sha256:2f15b3218f0552c60647ce60ada83632d2c09755b16259b13e3e4458e9ae419d` | `model_check.json` |
| Full tag digest | `sha256:845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` | `model_check.json` |
| Digest verification | All three confirmed to match the project handover record before generation ran (`comparison_with_handover.*` block, `model_check.json`) | `model_check.json` |
| Endpoint actually used (all 14 calls) | `http://127.0.0.1:42471/api/generate` — a per-job, dynamically assigned loopback port; **not** `localhost:11434` (the analysis script's unused default constant) — see §1(a) for the full, cross-checked evidence table | `run_record.json`; `job_record.json`; `run_log.jsonl`; `ollama_serve_32828822.log`; `stage2_qwen65.sbatch` |
| `raw` (templating bypass) | Not set in any of the 14 requests, so Ollama's standard ChatML templating was applied — see §1(c) | every saved request JSON (absent) |
| `system` field in the request | Not set by this pipeline's own code; the model's own default Modelfile system string was not overridden — see §1(c)–(d) for the full statement and its evidentiary limits | every saved request JSON (absent); `model_check.json` `show_modelfile`/`show_template` |
| `seed` | `42` — explicit in every request's `options`. **Prospective for this run only**; not a reconstruction of any historical seed and not a guarantee of exact cross-environment reproducibility | every saved request JSON; `run_record.json` `seed_note` |
| `temperature` | `0.2` | every saved request JSON |
| `top_p` | `0.9` | every saved request JSON |
| `num_ctx` (context window) | `32768` | every saved request JSON |
| `num_predict` (output cap) | `1800` for the 13 batch calls; `4200` for the final-synthesis call | every saved request JSON |
| `stream` | `false` | every saved request JSON |
| Retries / timeout | `RETRIES = 2`, backoff `5 + 5×attempt` s, `TIMEOUT_S = 900` s per HTTP call — **0 retries triggered across all 14 generations** | `code_copies/run_stage2_qwen.py` `generate()` (lines 52–53, 203–241) — the function that actually sent these requests for this run; mirrors, but is a separate implementation from, `01_local_qwen_metaverse_fincrime_analysis.py`'s `ollama_generate()` — see §1(a); cross-checked against `run_log.jsonl` (no `generate_error` events) |
| Batch size / count | 5 documents/batch, 13 batches, covering all 65 documents exactly once | `batch_plan.json`; `02_batch_document_mapping.csv` |
| `TOP_DOCS_FOR_FINAL` | 20 (documents ranked by `evidence_score`, metadata only, no excerpts) | `code_copies/run_stage2_qwen.py` line 51 |
| Driver Python | `3.6.15` (system `python3`), platform `Linux-5.14.21-150500.55.163-default-x86_64-with-glibc2.3.4` | `run_record.json` |
| Scheduler | an HPC batch job (scheduler, partition, node and account identifiers withheld), 1×NVIDIA H100, executed 2026-09-22, wall time 6 min 30 s, `COMPLETED`, exit code 0 | `qwen_65docs/qwen/STAGE2_completion_20260922.md`; `job_record.json` |
| Dependencies | Python standard library only (`csv`, `datetime`, `json`, `re`, `textwrap`, `time`, `urllib`, plus `argparse`/`hashlib`/`importlib.util`/`platform`/`socket` in the driver) — **no third-party Python packages** for the Qwen stage. Ollama 0.34.2 itself is the only external runtime dependency | direct inspection of `code_copies/*.py` import blocks |

All "Source" files in this table that are logs/records rather than
already-quoted code are now also in
`internal_reviewer_snapshot_20260929/verification/execution_logs/` and
`internal_reviewer_snapshot_20260929/verification/model_check.json` (see
§1(d) and that folder's listing in the snapshot's own README) — this table
does not depend on server-only paths to be checked.

## 6. Every request, indexed (13+1)

`02_request_response_index.csv` lists, for all 14 generations: the request
and response sha256 digests, byte sizes, Ollama's `done_reason`, and
`eval_count`/`prompt_eval_count` (output/input token counts as reported by
Ollama). All 14 rows show `done_reason=stop` — no truncated or retried
generation. `02_batch_document_mapping.csv` gives the 5 `doc_id`s behind
each of the 13 batch rows; the final-synthesis row's inputs are the 13
batch outputs plus the aggregate statistics plus the top-20 metadata
described in §3 above (not a per-document mapping in the same sense).

**Revised 2026-09-29: the saved request/response JSON files themselves are
now copied, unmodified, into this package** —
`internal_reviewer_snapshot_20260929/requests_responses/` holds all 28
files (14 requests + 14 responses), sha256-verified against their source at
`qwen_65docs/qwen/requests/` / `qwen_65docs/qwen/responses/`
(`internal_reviewer_snapshot_20260929/00_SOURCE_HASH_LEDGER.csv`). These are
the primary evidence this index is derived from — a reviewer who wants the
exact byte content of any single call should open the corresponding file in
that snapshot folder directly; the sha256 in this CSV index lets that be
verified without re-reading all 14 files. (An earlier version of this
section said these files were "not duplicated into this package" and
pointed only to the server-side `qwen_65docs/qwen/` paths — that is no
longer accurate as of this round and is corrected here.)

## 7. What is explicitly not claimed here

- **Endpoint/backend (§1(a)–(b)):** this file does not claim the source
  script's default endpoint (`localhost:11434`) was ever used for this run
  — the cross-checked evidence shows `127.0.0.1:42471` was used throughout.
  It does not claim `llama-server` is separately installed software or a
  third-party Ollama-compatible adapter — the log evidence shows it is
  Ollama's own bundled child process. It does not claim the actual
  post-template-rendered text sent from Ollama to `llama-server` was
  captured or observed — it was not; see §1(c).
- No separate/explicit `system` field was ever sent **by this pipeline's own
  request-building code** — see §1(c). This section does not invent a
  pipeline-authored system prompt to fill an expected table cell. It also
  does not claim the opposite — that no system prompt of any kind was in
  effect at inference time — see §1(c): the model's own default Modelfile
  system string was not overridden and was very likely applied by Ollama's
  standard template rendering (on the now-confirmed Ollama 0.34.2 +
  `llama-server` backend, §1(a)–(b)), though this was not directly observed
  on the raw token stream for this specific run.
- **This reasoning about default template/system behaviour is anchored
  specifically to the backend confirmed in §1(a)–(b) for this run** and
  should not be assumed to transfer to any other run or backend without
  equivalent direct log evidence.
- The digest/snippet template is fixed and identical across all 65
  documents; it is not a per-document customised prompt.
- This file transcribes the templates and configuration; it does not assess
  whether the resulting outputs are correct or well-grounded — that is
  `04_outputs_and_verification.md`'s and
  `qwen_65docs/review/02_synthesis_traceability.md`'s job (targeted
  claim-traceability and source checks, not an exhaustive claim-by-claim
  audit of every sentence — see that file's own scope note).
