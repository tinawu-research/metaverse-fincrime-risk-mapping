#!/usr/bin/env python3
"""
run_stage2_qwen.py  --  Stage (2) Qwen synthesis for the 65-document corpus (handover section 4.3 / 5.1 / 5.2).

What it does
  * Imports the EXISTING analysis script by path (never modified, no bytecode written) and reuses its
    QUESTION, MODEL, build_batch_prompt(), build_final_prompt(), make_doc_digest() unchanged.
  * Takes the Stage (1) preflight outputs as the ONLY document input
    (document_evidence_65.json: rule-based counts, relevance tiers, snippets, evidence_score).
  * Replays the Qwen portion of main() (package copy lines 357-419): batch_size 5 -> 13 batches over the
    doc_id-sorted list, num_predict 1800 per batch and 4200 for the final synthesis, retries=2 with
    5+5*attempt second backoff, urlopen timeout 900 s, options temperature 0.2 / top_p 0.9 / num_ctx 32768.
  * ONE deliberate difference from the historical request: options.seed = 42 (prospective setting, recorded).
  * Records everything: model identity check, batch plan, exact request payloads, raw responses, timing,
    retries, failures, effective configuration (run_record.json).
  * Input fit: every prompt is token-counted (/api/tokenize when available, else a conservative
    chars-per-token bound) and must satisfy prompt_tokens + num_predict <= num_ctx, otherwise the run aborts
    BEFORE sending (nothing is truncated silently).
  * Output completion: a batch is complete only if done == true, done_reason == "stop" and the text is
    non-empty. The final synthesis is NOT run unless all 13 batches are complete and cover all 65 doc_ids
    exactly once.
  * Never pulls, installs or substitutes a model. Aborts if the tag is absent.
  * Resume: with --resume, a batch whose stored response is complete AND whose stored request is byte-identical
    to the freshly built one is reused instead of regenerated (completed outputs are preserved).
Writes only under --out-dir.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import platform
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HANDOVER = {
    "model_tag": "qwen2.5:7b",
    "ollama_model_id": "845dbda0ea48",
    "model_layer_digest": "sha256:2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730",
    "config_digest": "sha256:2f15b3218f0552c60647ce60ada83632d2c09755b16259b13e3e4458e9ae419d",
}
BATCH_SIZE = 5
BATCH_NUM_PREDICT = 1800
FINAL_NUM_PREDICT = 4200
TOP_DOCS_FOR_FINAL = 20
RETRIES = 2            # documented: retries=2 -> at most 3 attempts
TIMEOUT_S = 900        # documented: urlopen(timeout=900)
OPTIONS_BASE = {"temperature": 0.2, "top_p": 0.9, "num_ctx": 32768}
FALLBACK_CHARS_PER_TOKEN = 2.8   # conservative lower bound used only if /api/tokenize is unavailable


def now():
    return dt.datetime.now().isoformat(timespec="seconds")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(p):
    h = hashlib.sha256()
    with open(str(p), "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def log_event(log_path, **ev):
    ev = dict(ts=now(), **ev)
    with open(str(log_path), "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    print(json.dumps(ev, ensure_ascii=False), flush=True)


def load_module(script):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("qwen_stage2_module", str(script))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for name in ("QUESTION", "MODEL", "OLLAMA_URL", "LEXICONS", "build_batch_prompt", "build_final_prompt", "make_doc_digest"):
        if not hasattr(mod, name):
            raise SystemExit("analysis script lacks expected symbol: " + name)
    return mod


def http_json(url, payload=None, timeout=60):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"},
                                 method="GET" if payload is None else "POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, json.loads(body) if body.strip() else {}


# ----------------------------------------------------------------------------------------------------------
def model_identity_check(base, model, out_dir):
    result = {"checked_at": now(), "endpoint_base": base, "model_tag_requested": model}
    _, ver = http_json(base + "/api/version")
    result["ollama_version"] = ver.get("version")
    _, tags = http_json(base + "/api/tags")
    entry = None
    for m in tags.get("models", []):
        if m.get("name") == model or m.get("model") == model:
            entry = m
            break
    result["model_tag_present"] = entry is not None
    result["models_on_server"] = [m.get("name") for m in tags.get("models", [])]
    if entry is None:
        result["blocker"] = "model tag %s is not present on the server; no pull performed" % model
        write_json(out_dir / "model_check.json", result)
        return result
    result["tags_entry"] = entry
    tag_digest = entry.get("digest", "")
    _, show = http_json(base + "/api/show", {"model": model}, timeout=120)
    result["show_details"] = show.get("details")
    result["show_parameters"] = show.get("parameters")
    result["show_template"] = show.get("template")
    result["show_modelfile"] = show.get("modelfile")
    mi = show.get("model_info") or {}
    result["show_model_info_subset"] = {k: v for k, v in mi.items()
                                        if any(s in k for s in ("architecture", "context_length", "parameter_count",
                                                                "file_type", "block_count", "embedding_length",
                                                                "basename", "size_label", "finetune", "quantization"))}
    blobs = re.findall(r"sha256[-:]([0-9a-f]{64})", show.get("modelfile", "") or "")
    layer_digests = ["sha256:" + b for b in dict.fromkeys(blobs)]
    result["blob_digests_in_modelfile"] = layer_digests
    result["comparison_with_handover"] = {
        "handover": HANDOVER,
        "server_tag_digest": tag_digest,
        "tag_digest_prefix_equals_handover_model_id": tag_digest.startswith(HANDOVER["ollama_model_id"]),
        "handover_model_layer_digest_in_modelfile": HANDOVER["model_layer_digest"] in layer_digests,
        "handover_config_digest_visible_via_api": False,
        "note": ("Ollama's /api/tags digest is the manifest digest whose first 12 hex chars are the `ollama list` ID. "
                 "The GGUF model-layer digest appears as the FROM blob in the modelfile. The config-layer digest is not "
                 "exposed by the HTTP API; it is only checkable from the manifest file on the server's model store."),
    }
    write_json(out_dir / "model_check.json", result)
    return result


# ----------------------------------------------------------------------------------------------------------
class Tokenizer:
    def __init__(self, base, model, log_path):
        self.base, self.model, self.log_path = base, model, log_path
        self.available = None
        self.max_ratio = None      # observed prompt_eval_count / prompt_chars, calibrated from real responses
        self.calibration = []

    def calibrate(self, prompt_chars, prompt_eval_count):
        """Learn tokens-per-char from a real response. Ignore implausibly low counts (prefix-cache reuse or
        server-side truncation would under-report), i.e. fewer than one token per 8 characters."""
        if not prompt_chars or not prompt_eval_count:
            return
        r = prompt_eval_count / float(prompt_chars)
        self.calibration.append({"prompt_chars": prompt_chars, "prompt_eval_count": prompt_eval_count, "ratio": round(r, 5)})
        if r >= 1.0 / 8.0:
            self.max_ratio = max(self.max_ratio or 0.0, r)

    def count(self, text):
        if self.available is not False:
            try:
                status, d = http_json(self.base + "/api/tokenize", {"model": self.model, "prompt": text}, timeout=300)
                if "tokens" in d:
                    self.available = True
                    return len(d["tokens"]), "api_tokenize"
            except urllib.error.HTTPError as e:
                if self.available is None:
                    log_event(self.log_path, event="tokenize_unavailable", http_status=e.code)
                self.available = False
            except Exception as e:  # noqa
                if self.available is None:
                    log_event(self.log_path, event="tokenize_unavailable", error=repr(e))
                self.available = False
        if self.max_ratio:
            return int(len(text) * self.max_ratio * 1.10) + 1, "calibrated_max_observed_ratio_x1.10(%.5f)" % self.max_ratio
        return int(len(text) / FALLBACK_CHARS_PER_TOKEN) + 1, "chars/%.1f_upper_bound" % FALLBACK_CHARS_PER_TOKEN


def fit_check(tok, prompt, num_predict, label, log_path):
    n, method = tok.count(prompt)
    budget = OPTIONS_BASE["num_ctx"]
    ok = n + num_predict <= budget
    rec = {"label": label, "prompt_chars": len(prompt), "prompt_tokens_estimate": n, "estimate_method": method,
           "num_predict": num_predict, "num_ctx": budget, "fits": ok}
    log_event(log_path, event="input_fit_check", **rec)
    return ok, rec


def generate(base_url, payload, log_path, label):
    """Mirror of ollama_generate() (script lines 175-203) with full-response capture and per-attempt logging."""
    data = json.dumps(payload).encode("utf-8")
    attempts = []
    last_error = None
    for attempt in range(RETRIES + 1):
        t0 = time.time()
        started = now()
        try:
            req = urllib.request.Request(base_url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as response:
                status = response.status
                raw = response.read().decode("utf-8", errors="replace")
            parsed = json.loads(raw)
            wall = round(time.time() - t0, 3)
            attempts.append({"attempt": attempt + 1, "started": started, "finished": now(), "wall_seconds": wall,
                             "http_status": status, "ok": True})
            log_event(log_path, event="generate_ok", label=label, attempt=attempt + 1, wall_seconds=wall,
                      done=parsed.get("done"), done_reason=parsed.get("done_reason"),
                      prompt_eval_count=parsed.get("prompt_eval_count"), eval_count=parsed.get("eval_count"))
            return parsed, attempts
        except urllib.error.HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="replace")[:2000]
            except Exception:  # noqa
                pass
            last_error = "HTTPError %s: %s" % (exc.code, body)
        except (urllib.error.URLError, OSError, ValueError) as exc:  # socket.timeout is OSError on py3.6
            last_error = "%s: %s" % (type(exc).__name__, exc)
        wall = round(time.time() - t0, 3)
        attempts.append({"attempt": attempt + 1, "started": started, "finished": now(), "wall_seconds": wall,
                         "ok": False, "error": last_error})
        log_event(log_path, event="generate_error", label=label, attempt=attempt + 1, error=last_error, wall_seconds=wall)
        if attempt < RETRIES:
            time.sleep(5 + attempt * 5)
    raise RuntimeError("Ollama generation failed after %d attempts: %s" % (RETRIES + 1, last_error), attempts)


def is_complete(parsed):
    text = (parsed.get("response") or "").strip()
    return bool(text) and parsed.get("done") is True and parsed.get("done_reason") == "stop"


# ----------------------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--evidence-json", required=True, help="preflight document_evidence_65.json")
    ap.add_argument("--preflight-manifest", required=True, help="preflight manifest_65.json (cross-check only)")
    ap.add_argument("--input-txt", required=True, help="preflight all_extracted_text_65docs.txt (path + sha256 recorded)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--endpoint", default=None, help="full /api/generate URL; default = OLLAMA_URL constant of the script")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dry-run", action="store_true", help="build plan, prompts, fit checks and request files; send nothing")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--stop-after-batch", type=int, default=0,
                    help="operational check: stop (exit 0) after this batch completes; synthesis is not attempted")
    a = ap.parse_args()

    out = Path(a.out_dir)
    (out / "requests").mkdir(parents=True, exist_ok=True)
    (out / "responses").mkdir(parents=True, exist_ok=True)
    log_path = out / "run_log.jsonl"
    mod = load_module(a.script)
    endpoint = a.endpoint or mod.OLLAMA_URL
    base = endpoint.rsplit("/api/", 1)[0]
    model = mod.MODEL
    run_started = now()
    log_event(log_path, event="run_start", dry_run=a.dry_run, resume=a.resume, endpoint=endpoint, model=model, seed=a.seed)

    # ---- inputs (preflight outputs only) ----
    analyses = read_json(a.evidence_json)
    ids = [x["doc_id"] for x in analyses]
    if len(ids) != 65 or len(set(ids)) != 65:
        raise SystemExit("expected 65 unique doc_ids in evidence json, got %d/%d" % (len(ids), len(set(ids))))
    if ids != sorted(ids):
        raise SystemExit("evidence json is not sorted by doc_id; refusing (batch membership must follow main() order)")
    for x in analyses:
        if x.get("evidence_score") != sum(x["category_totals"].values()):
            raise SystemExit("evidence_score mismatch for " + x["doc_id"])

    input_file = Path(a.input_txt)
    aggregate_stats = {
        "input_file": str(input_file),
        "input_size_bytes": input_file.stat().st_size,
        "document_count": len(analyses),
        "total_extracted_words_reported": sum(int(x["extracted_words"] or 0) for x in analyses if str(x["extracted_words"]).isdigit()),
        "category_totals": {c: sum(x["category_totals"][c] for x in analyses) for c in mod.LEXICONS},
        "relevance_counts": {},
        "analysis_question": mod.QUESTION,
        "model": mod.MODEL,
        "cost_boundary": "Local Ollama/Qwen only. No paid API and no Zep graph build.",
    }
    for x in analyses:
        aggregate_stats["relevance_counts"][x["relevance"]] = aggregate_stats["relevance_counts"].get(x["relevance"], 0) + 1
    pre = read_json(a.preflight_manifest)
    for k in ("document_count", "total_extracted_words_reported", "category_totals", "relevance_counts", "input_size_bytes"):
        if pre.get(k) != aggregate_stats[k]:
            raise SystemExit("aggregate_stats[%s] differs from preflight manifest" % k)
    log_event(log_path, event="inputs_verified", documents=len(analyses), relevance_counts=aggregate_stats["relevance_counts"],
              input_sha256=sha256_file(input_file))

    # ---- batch plan (identical slicing to main()) ----
    batches = [analyses[i:i + BATCH_SIZE] for i in range(0, len(analyses), BATCH_SIZE)]
    plan = {"batch_size": BATCH_SIZE, "batch_count": len(batches), "document_order": ids,
            "batches": [{"batch": i + 1, "doc_ids": [x["doc_id"] for x in b]} for i, b in enumerate(batches)]}
    write_json(out / "batch_plan.json", plan)
    covered = [d for b in batches for d in [x["doc_id"] for x in b]]
    if covered != ids:
        raise SystemExit("batch plan does not cover the 65 documents exactly once")

    options_batch = dict(OPTIONS_BASE, num_predict=BATCH_NUM_PREDICT, seed=a.seed)
    options_final = dict(OPTIONS_BASE, num_predict=FINAL_NUM_PREDICT, seed=a.seed)

    # ---- model identity (skipped in dry-run only if server unreachable) ----
    model_check = None
    try:
        model_check = model_identity_check(base, model, out)
        log_event(log_path, event="model_check", ollama_version=model_check.get("ollama_version"),
                  present=model_check.get("model_tag_present"),
                  comparison=model_check.get("comparison_with_handover"))
    except Exception as exc:  # noqa
        log_event(log_path, event="model_check_failed", error=repr(exc))
        if not a.dry_run:
            raise SystemExit("cannot reach Ollama endpoint for model identity check: %r" % (exc,))
    if model_check is not None and not model_check.get("model_tag_present") and not a.dry_run:
        raise SystemExit("BLOCKER: " + model_check.get("blocker", "model missing"))
    if model_check is not None and model_check.get("model_tag_present") and not a.dry_run:
        cmp = model_check["comparison_with_handover"]
        if not (cmp["tag_digest_prefix_equals_handover_model_id"] and cmp["handover_model_layer_digest_in_modelfile"]):
            write_json(out / "status.json", {"stage": "stopped_model_identity_mismatch", "finished": now(), "comparison": cmp})
            raise SystemExit("STOP: model identity differs from the handover record; no generation performed: %s" % json.dumps(cmp))

    tok = Tokenizer(base, model, log_path)
    fit_records = []

    # ---- batches ----
    batch_outputs = []
    incomplete = []
    for idx, batch in enumerate(batches, start=1):
        label = "qwen_batch_%02d" % idx
        prompt = mod.build_batch_prompt(batch, idx, len(batches))
        payload = {"model": model, "prompt": prompt, "stream": False, "options": options_batch}
        req_path = out / "requests" / (label + "_request.json")
        resp_path = out / "responses" / (label + "_response.json")
        req_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        req_sha = sha256_bytes(req_bytes)

        if a.resume and resp_path.exists() and req_path.exists():
            stored = read_json(resp_path)
            if stored.get("request_sha256") == req_sha and is_complete(stored.get("raw_response", {})):
                log_event(log_path, event="batch_reused", label=label, request_sha256=req_sha)
                batch_outputs.append({"batch": idx, "doc_ids": [x["doc_id"] for x in batch],
                                      "summary": stored["raw_response"]["response"].strip()})
                fit_records.append(stored.get("fit_check"))
                tok.calibrate(len(prompt), stored["raw_response"].get("prompt_eval_count"))
                if a.stop_after_batch and idx >= a.stop_after_batch:
                    write_json(out / "status.json", {"stage": "operational_check_batch_%d_reused_complete" % idx, "finished": now()})
                    log_event(log_path, event="stop_after_batch", batch=idx, reused=True)
                    return
                continue

        req_path.write_bytes(req_bytes)
        ok, fit = fit_check(tok, prompt, BATCH_NUM_PREDICT, label, log_path)
        fit_records.append(fit)
        if not ok:
            raise SystemExit("INPUT DOES NOT FIT for %s: %s (nothing sent, nothing truncated)" % (label, fit))
        if a.dry_run:
            continue
        try:
            parsed, attempts = generate(endpoint, payload, log_path, label)
        except RuntimeError as exc:
            write_json(resp_path.with_suffix(".failed.json"), {"label": label, "request_sha256": req_sha,
                                                               "error": str(exc.args[0]), "attempts": exc.args[1]})
            raise SystemExit("FAILED %s after documented retries; completed outputs preserved. %s" % (label, exc.args[0]))
        text = (parsed.get("response") or "").strip()
        complete = is_complete(parsed)
        tok.calibrate(len(prompt), parsed.get("prompt_eval_count"))
        pec = parsed.get("prompt_eval_count") or 0
        if pec < 0.5 * fit["prompt_tokens_estimate"]:
            log_event(log_path, event="prompt_eval_count_low", label=label, prompt_eval_count=pec,
                      estimate=fit["prompt_tokens_estimate"],
                      note="far below estimate: prefix-cache reuse or server-side truncation; inspect before relying on this batch")
        record = {"label": label, "batch": idx, "doc_ids": [x["doc_id"] for x in batch], "request_sha256": req_sha,
                  "request_file": str(req_path), "options_sent": options_batch, "attempts": attempts,
                  "fit_check": fit, "complete": complete, "done_reason": parsed.get("done_reason"),
                  "prompt_eval_count": parsed.get("prompt_eval_count"), "eval_count": parsed.get("eval_count"),
                  "raw_response": parsed}
        write_json(resp_path, record)
        (out / (label + ".md")).write_text(text, encoding="utf-8")
        if not complete:
            incomplete.append({"label": label, "done": parsed.get("done"), "done_reason": parsed.get("done_reason"),
                               "eval_count": parsed.get("eval_count"), "empty": not text})
        batch_outputs.append({"batch": idx, "doc_ids": [x["doc_id"] for x in batch], "summary": text})
        if a.stop_after_batch and idx >= a.stop_after_batch:
            st = {"stage": "operational_check_batch_%d_%s" % (idx, "complete" if complete else "INCOMPLETE"),
                  "finished": now(), "complete": complete, "done_reason": parsed.get("done_reason"),
                  "eval_count": parsed.get("eval_count"), "prompt_eval_count": parsed.get("prompt_eval_count"),
                  "wall_seconds": attempts[-1]["wall_seconds"]}
            write_json(out / "status.json", st)
            log_event(log_path, event="stop_after_batch", **st)
            sys.exit(0 if complete else 6)

    if a.dry_run:
        final_prompt_preview = mod.build_final_prompt("(batch summaries not yet generated)", aggregate_stats,
                                                      sorted(analyses, key=lambda x: x["evidence_score"], reverse=True)[:TOP_DOCS_FOR_FINAL])
        (out / "requests" / "final_synthesis_request_PREVIEW_dry_run.txt").write_text(final_prompt_preview, encoding="utf-8")
        write_json(out / "status.json", {"stage": "dry_run", "finished": now(), "batches_planned": len(batches),
                                         "fit_checks": fit_records, "model_check_present": model_check.get("model_tag_present") if model_check else None})
        log_event(log_path, event="dry_run_done")
        return

    # ---- coverage / completion gate ----
    done_ids = [d for b in batch_outputs for d in b["doc_ids"]]
    coverage_ok = sorted(done_ids) == sorted(ids) and len(done_ids) == 65
    md_nonempty = all((out / ("qwen_batch_%02d.md" % b["batch"])).exists() and
                      (out / ("qwen_batch_%02d.md" % b["batch"])).stat().st_size > 0 for b in batch_outputs)
    batch_summary_md = "\n\n".join("## Batch %d (%s)\n\n%s" % (b["batch"], ", ".join(b["doc_ids"]), b["summary"]) for b in batch_outputs)
    (out / "qwen_batch_summaries.md").write_text(batch_summary_md, encoding="utf-8")
    gate = {"batches_completed": len(batch_outputs), "batches_planned": len(batches), "coverage_65_exactly_once": coverage_ok,
            "all_batch_md_nonempty": md_nonempty, "incomplete_batches": incomplete}
    log_event(log_path, event="synthesis_gate", **gate)
    if not (coverage_ok and md_nonempty and not incomplete and len(batch_outputs) == len(batches)):
        write_json(out / "status.json", {"stage": "batches_done_synthesis_withheld", "finished": now(), "gate": gate,
                                         "reason": "one or more batches incomplete (done_reason != stop or empty) or coverage failed; "
                                                   "final synthesis deliberately NOT generated over incomplete batches"})
        log_event(log_path, event="synthesis_withheld", **gate)
        sys.exit(3)

    # ---- final synthesis ----
    top_docs = sorted(analyses, key=lambda x: x["evidence_score"], reverse=True)[:TOP_DOCS_FOR_FINAL]
    final_prompt = mod.build_final_prompt(batch_summary_md, aggregate_stats, top_docs)
    payload = {"model": model, "prompt": final_prompt, "stream": False, "options": options_final}
    req_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    (out / "requests" / "final_synthesis_request.json").write_bytes(req_bytes)
    ok, fit = fit_check(tok, final_prompt, FINAL_NUM_PREDICT, "final_synthesis", log_path)
    fit_records.append(fit)
    if not ok:
        write_json(out / "status.json", {"stage": "final_prompt_does_not_fit", "finished": now(), "fit": fit})
        raise SystemExit("FINAL PROMPT DOES NOT FIT num_ctx: %s (nothing sent, nothing truncated)" % fit)
    try:
        parsed, attempts = generate(endpoint, payload, log_path, "final_synthesis")
    except RuntimeError as exc:
        write_json(out / "responses" / "final_synthesis_response.failed.json", {"error": str(exc.args[0]), "attempts": exc.args[1]})
        write_json(out / "status.json", {"stage": "final_synthesis_failed", "finished": now(), "error": str(exc.args[0])})
        raise SystemExit("FAILED final synthesis after documented retries; batch outputs preserved.")
    final_text = (parsed.get("response") or "").strip()
    final_complete = is_complete(parsed)
    write_json(out / "responses" / "final_synthesis_response.json",
               {"label": "final_synthesis", "request_sha256": sha256_bytes(req_bytes), "options_sent": options_final,
                "attempts": attempts, "fit_check": fit, "complete": final_complete, "done_reason": parsed.get("done_reason"),
                "prompt_eval_count": parsed.get("prompt_eval_count"), "eval_count": parsed.get("eval_count"),
                "top_docs_by_evidence_score": [x["doc_id"] for x in top_docs], "raw_response": parsed})
    (out / "final_synthesis.md").write_text(final_text, encoding="utf-8")

    # ---- report in the historical format (main() lines 378-419) ----
    doc_evidence_appendix = "\n\n".join(
        "### {doc_id} - {filename}\n\nRelevance: {relevance}\n\nTop evidence:\n{snippets}".format(
            doc_id=item["doc_id"], filename=item["filename"], relevance=item["relevance"],
            snippets="\n".join("- " + s["text"] for s in item["snippets"][:4]) or "- No high-scoring evidence sentence extracted.")
        for item in analyses)
    report = """# Local Qwen Analysis: Metaverse, Cryptocurrency, and Financial Crime

**Research question:** {q}

**Cost and privacy boundary:** This run used local Ollama/Qwen only. It did not use paid API calls and did not run MiroFish's Zep Cloud graph-building stage.

**Corpus:** `{corpus}`

**Corpus size:** {size:,} bytes across {n} parsed documents, with {words:,} reported extracted words.

**Generated:** {gen}

## Final Synthesis

{final}

## Aggregate Evidence Profile

```json
{agg}
```

## Qwen Batch Summaries

{batches}

## Document Evidence Appendix

{appendix}
""".format(q=mod.QUESTION, corpus=str(input_file), size=aggregate_stats["input_size_bytes"], n=aggregate_stats["document_count"],
           words=aggregate_stats["total_extracted_words_reported"], gen=now(), final=final_text,
           agg=json.dumps(aggregate_stats, ensure_ascii=False, indent=2), batches=batch_summary_md, appendix=doc_evidence_appendix)
    (out / "complete_analysis_report.md").write_text(report, encoding="utf-8")

    # ---- run record (handover 5.2) ----
    cpu = ""
    try:
        for line in open("/proc/cpuinfo", encoding="utf-8", errors="replace"):
            if line.lower().startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
    except Exception:  # noqa
        pass
    ps = {}
    try:
        _, ps = http_json(base + "/api/ps")
    except Exception:  # noqa
        pass
    resp_files = sorted((out / "responses").glob("qwen_batch_*_response.json"))
    batch_records = [read_json(p) for p in resp_files]
    run_record = {
        "run_started": run_started, "run_finished": now(),
        "endpoint": endpoint, "ollama_version": model_check.get("ollama_version") if model_check else None,
        "model_tag": model,
        "model_identity": model_check.get("comparison_with_handover") if model_check else None,
        "seed": a.seed,
        "seed_note": ("seed=42 is a prospective setting for this run only. The historical 2026-05 request carried no seed and its "
                      "effective seed is unknown; setting a seed does not reconstruct it and does not guarantee verbatim "
                      "reproducibility across hardware or Ollama versions."),
        "options_batch": options_batch, "options_final": options_final, "keep_alive": "server default (not set in request)",
        "batch_size": BATCH_SIZE, "batch_count": len(batches), "retries": RETRIES, "backoff_seconds": "5 + 5*attempt",
        "urlopen_timeout_seconds": TIMEOUT_S,
        "prompt_templates": "build_batch_prompt()/build_final_prompt()/make_doc_digest() imported unchanged from the analysis script",
        "analysis_script": a.script, "analysis_script_sha256": sha256_file(a.script),
        "evidence_json": a.evidence_json, "evidence_json_sha256": sha256_file(a.evidence_json),
        "input_file": str(input_file), "input_sha256": sha256_file(input_file),
        "python": sys.version, "platform": platform.platform(), "hostname": socket.gethostname(), "cpu": cpu,
        "ollama_ps_after_run": ps,
        "batches": [{"batch": r["batch"], "doc_ids": r["doc_ids"], "attempts": r["attempts"], "complete": r["complete"],
                     "done_reason": r["done_reason"], "prompt_eval_count": r["prompt_eval_count"], "eval_count": r["eval_count"],
                     "fit_check": r["fit_check"],
                     "total_duration_s": round((r["raw_response"].get("total_duration") or 0) / 1e9, 3),
                     "load_duration_s": round((r["raw_response"].get("load_duration") or 0) / 1e9, 3)} for r in batch_records],
        "final_synthesis": {"attempts": attempts, "complete": final_complete, "done_reason": parsed.get("done_reason"),
                            "prompt_eval_count": parsed.get("prompt_eval_count"), "eval_count": parsed.get("eval_count"),
                            "fit_check": fit, "total_duration_s": round((parsed.get("total_duration") or 0) / 1e9, 3)},
        "coverage": gate,
        "tokenizer_calibration": {"api_tokenize_available": tok.available, "max_observed_ratio": tok.max_ratio,
                                  "observations": tok.calibration},
        "qwen_generations_total": len(batch_records) + 1,
    }
    write_json(out / "run_record.json", run_record)
    write_json(out / "status.json", {"stage": "stage2_complete" if final_complete else "stage2_final_incomplete",
                                     "finished": now(), "final_done_reason": parsed.get("done_reason"), "gate": gate})
    log_event(log_path, event="run_done", final_complete=final_complete, final_done_reason=parsed.get("done_reason"))


if __name__ == "__main__":
    main()
