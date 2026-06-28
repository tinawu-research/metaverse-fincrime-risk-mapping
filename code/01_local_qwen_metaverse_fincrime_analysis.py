import csv
import datetime as dt
import json
import re
import textwrap
import time
import urllib.error
import urllib.request
from pathlib import Path


INPUT_FILE = Path(
    r"C:\Users\mtiwar05\OneDrive - Charles Sturt University\CSU\Metaverse and Cryptocurrencies\Analysis\Codex\Results\Round 5\all_extracted_text_by_pdf.txt"
)
QUESTION = (
    "How do the combined features of metaverse platforms and cryptocurrency ecosystems "
    "generate new money laundering and other financial crime opportunities, and subsequently "
    "help model, analyse, and identify intervention points within these emerging financial crime environments?"
)
MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434/api/generate"


LEXICONS = {
    "metaverse_platform_features": [
        "metaverse", "virtual world", "virtual worlds", "avatar", "avatars", "vr", "ar", "xr",
        "immersive", "3d", "digital twin", "digital twins", "virtual real estate", "virtual property",
        "virtual asset", "virtual assets", "nft", "nfts", "marketplace", "interoperability",
        "identity", "self-sovereign", "pseudonym", "anonymous", "privacy", "social interaction",
        "gaming", "persistent", "spatial", "edge computing", "iot", "ai", "agent"
    ],
    "crypto_ecosystem_features": [
        "cryptocurrency", "cryptocurrencies", "crypto", "blockchain", "wallet", "wallets",
        "exchange", "exchanges", "dex", "defi", "token", "tokens", "stablecoin", "stablecoins",
        "smart contract", "smart contracts", "dao", "daos", "bridge", "bridges", "mixer",
        "mixers", "tumbler", "tumblers", "privacy coin", "privacy coins", "on-chain", "off-chain",
        "transaction", "transactions", "custody", "oracle", "gas", "ledger"
    ],
    "financial_crime_opportunities": [
        "money laundering", "laundering", "aml", "financial crime", "financial crimes",
        "fraud", "scam", "scams", "phishing", "terrorist financing", "cft", "sanctions",
        "illicit", "illegal", "cybercrime", "theft", "ransom", "ransomware", "market manipulation",
        "tax evasion", "grey economy", "black market", "predicate offence", "crime"
    ],
    "modelling_analysis_intervention": [
        "kyc", "know your customer", "cdd", "customer due diligence", "regulation", "regulatory",
        "compliance", "monitoring", "detection", "detect", "traceability", "traceable", "forensic",
        "analytics", "machine learning", "ml", "artificial intelligence", "ai", "graph", "network",
        "anomaly", "risk", "risk assessment", "typology", "intervention", "governance",
        "identity verification", "transaction monitoring", "audit", "smart contract audit",
        "prevention", "law enforcement", "supervision"
    ],
}


def normalise_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_documents(text: str):
    matches = list(re.finditer(r"(?m)^DOC_ID:\s*(.+?)\s*$", text))
    documents = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section = text[start:end].strip()
        lines = section.splitlines()
        metadata = {"doc_id": match.group(1).strip(), "filename": "", "pages": "", "extracted_words": ""}
        body_start = 0
        for idx, line in enumerate(lines[:12]):
            if line.startswith("FILENAME:"):
                metadata["filename"] = line.split(":", 1)[1].strip()
            elif line.startswith("PAGES:"):
                metadata["pages"] = line.split(":", 1)[1].strip()
            elif line.startswith("EXTRACTED_WORDS:"):
                metadata["extracted_words"] = line.split(":", 1)[1].strip()
                body_start = idx + 1
                break
        body = "\n".join(lines[body_start:]).strip()
        documents.append({**metadata, "text": body})
    return documents


def count_terms(text_lower: str, terms):
    total = 0
    hits = {}
    for term in terms:
        pattern = r"\b" + re.escape(term.lower()) + r"\b"
        count = len(re.findall(pattern, text_lower))
        if count:
            hits[term] = count
            total += count
    return total, hits


def sentence_split(text: str):
    chunks = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
    return [normalise_space(c) for c in chunks if len(normalise_space(c)) >= 70]


def score_sentence(sentence: str):
    low = sentence.lower()
    category_counts = {}
    score = 0
    categories_hit = 0
    for category, terms in LEXICONS.items():
        count, _ = count_terms(low, terms)
        category_counts[category] = count
        if count:
            categories_hit += 1
        weight = 3 if category == "financial_crime_opportunities" else 2
        score += count * weight
    score += categories_hit * 2
    if category_counts["metaverse_platform_features"] and category_counts["crypto_ecosystem_features"]:
        score += 3
    if category_counts["financial_crime_opportunities"] and category_counts["modelling_analysis_intervention"]:
        score += 3
    return score, category_counts


def analyse_document(doc):
    text = doc["text"]
    low = text.lower()
    category_hits = {}
    category_totals = {}
    for category, terms in LEXICONS.items():
        total, hits = count_terms(low, terms)
        category_totals[category] = total
        category_hits[category] = hits

    ranked = []
    for sentence in sentence_split(text):
        score, counts = score_sentence(sentence)
        if score > 0:
            ranked.append((score, counts, sentence))
    ranked.sort(key=lambda item: item[0], reverse=True)

    selected = []
    seen = set()
    for score, counts, sentence in ranked:
        compact = sentence[:700]
        key = compact[:120].lower()
        if key in seen:
            continue
        seen.add(key)
        selected.append({"score": score, "category_counts": counts, "text": compact})
        if len(selected) >= 7:
            break

    score_total = sum(category_totals.values())
    if category_totals["financial_crime_opportunities"] >= 15 and category_totals["crypto_ecosystem_features"] >= 15:
        relevance = "primary financial-crime/crypto evidence"
    elif score_total >= 80:
        relevance = "highly relevant platform/security evidence"
    elif score_total >= 25:
        relevance = "supporting contextual evidence"
    else:
        relevance = "peripheral or background evidence"

    return {
        "doc_id": doc["doc_id"],
        "filename": doc["filename"],
        "pages": doc["pages"],
        "extracted_words": doc["extracted_words"],
        "category_totals": category_totals,
        "top_terms": {
            category: sorted(hits.items(), key=lambda kv: kv[1], reverse=True)[:8]
            for category, hits in category_hits.items()
        },
        "relevance": relevance,
        "snippets": selected,
    }


def ollama_generate(prompt: str, max_tokens: int = 1800, retries: int = 2):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,
            "num_ctx": 32768,
            "num_predict": max_tokens,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    last_error = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                OLLAMA_URL,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=900) as response:
                parsed = json.loads(response.read().decode("utf-8", errors="replace"))
            return parsed.get("response", "").strip()
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(5 + attempt * 5)
    raise RuntimeError(f"Ollama generation failed: {last_error}")


def make_doc_digest(item):
    snippets = "\n".join(
        f"- Evidence {idx + 1}: {snippet['text']}"
        for idx, snippet in enumerate(item["snippets"][:5])
    )
    top_terms = "; ".join(
        f"{category}: " + ", ".join(f"{term}={count}" for term, count in terms[:5])
        for category, terms in item["top_terms"].items()
        if terms
    )
    return textwrap.dedent(
        f"""
        {item['doc_id']} | {item['filename']}
        Pages: {item['pages']} | extracted words: {item['extracted_words']} | relevance: {item['relevance']}
        Category totals: {json.dumps(item['category_totals'], ensure_ascii=False)}
        Top terms: {top_terms}
        {snippets}
        """
    ).strip()


def build_batch_prompt(batch_items, batch_index, batch_count):
    docs_text = "\n\n---\n\n".join(make_doc_digest(item) for item in batch_items)
    return f"""
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
""".strip()


def build_final_prompt(batch_summaries, aggregate_stats, top_docs):
    top_doc_text = "\n".join(
        f"- {item['doc_id']}: {item['filename']} | {item['relevance']} | {item['category_totals']}"
        for item in top_docs
    )
    return f"""
You are writing the final synthesis for an academic research analysis.

Research question:
{QUESTION}

Method boundary: The corpus was analysed locally with qwen2.5:7b through Ollama. Do not imply any cloud or paid API use.
Use only the batch summaries and aggregate evidence supplied below. Cite DOC_IDs where useful.

Aggregate corpus statistics:
{json.dumps(aggregate_stats, ensure_ascii=False, indent=2)}

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
""".strip()


def write_csv(path, analyses):
    fieldnames = [
        "doc_id",
        "filename",
        "pages",
        "extracted_words",
        "relevance",
        "metaverse_platform_features",
        "crypto_ecosystem_features",
        "financial_crime_opportunities",
        "modelling_analysis_intervention",
        "top_evidence_1",
        "top_evidence_2",
        "top_evidence_3",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in analyses:
            row = {
                "doc_id": item["doc_id"],
                "filename": item["filename"],
                "pages": item["pages"],
                "extracted_words": item["extracted_words"],
                "relevance": item["relevance"],
                **item["category_totals"],
            }
            for idx in range(3):
                row[f"top_evidence_{idx + 1}"] = item["snippets"][idx]["text"] if idx < len(item["snippets"]) else ""
            writer.writerow(row)


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    run_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = INPUT_FILE.parent / f"mirofish_local_qwen_free_analysis_{run_id}"
    output_dir.mkdir(parents=True, exist_ok=False)

    corpus = INPUT_FILE.read_text(encoding="utf-8", errors="replace")
    documents = parse_documents(corpus)
    analyses = [analyse_document(doc) for doc in documents]

    for item in analyses:
        item["evidence_score"] = sum(item["category_totals"].values())
    analyses.sort(key=lambda item: item["doc_id"])

    aggregate_stats = {
        "input_file": str(INPUT_FILE),
        "input_size_bytes": INPUT_FILE.stat().st_size,
        "document_count": len(analyses),
        "total_extracted_words_reported": sum(int(a["extracted_words"] or 0) for a in analyses if str(a["extracted_words"]).isdigit()),
        "category_totals": {
            category: sum(item["category_totals"][category] for item in analyses)
            for category in LEXICONS
        },
        "relevance_counts": {},
        "analysis_question": QUESTION,
        "model": MODEL,
        "cost_boundary": "Local Ollama/Qwen only. No paid API and no Zep graph build.",
    }
    for item in analyses:
        aggregate_stats["relevance_counts"][item["relevance"]] = aggregate_stats["relevance_counts"].get(item["relevance"], 0) + 1

    write_csv(output_dir / "document_evidence_table.csv", analyses)
    (output_dir / "document_evidence.json").write_text(json.dumps(analyses, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "manifest.json").write_text(json.dumps(aggregate_stats, ensure_ascii=False, indent=2), encoding="utf-8")

    batch_size = 5
    batches = [analyses[i:i + batch_size] for i in range(0, len(analyses), batch_size)]
    batch_outputs = []
    for idx, batch in enumerate(batches, start=1):
        print(f"Running local Qwen batch {idx}/{len(batches)} for {', '.join(item['doc_id'] for item in batch)}", flush=True)
        prompt = build_batch_prompt(batch, idx, len(batches))
        output = ollama_generate(prompt, max_tokens=1800)
        batch_outputs.append({"batch": idx, "doc_ids": [item["doc_id"] for item in batch], "summary": output})
        (output_dir / f"qwen_batch_{idx:02d}.md").write_text(output, encoding="utf-8")

    batch_summary_md = "\n\n".join(
        f"## Batch {item['batch']} ({', '.join(item['doc_ids'])})\n\n{item['summary']}"
        for item in batch_outputs
    )
    (output_dir / "qwen_batch_summaries.md").write_text(batch_summary_md, encoding="utf-8")

    top_docs = sorted(analyses, key=lambda item: item["evidence_score"], reverse=True)[:20]
    print("Running final local Qwen synthesis", flush=True)
    final_prompt = build_final_prompt(batch_summary_md, aggregate_stats, top_docs)
    final_synthesis = ollama_generate(final_prompt, max_tokens=4200)

    doc_evidence_appendix = "\n\n".join(
        "### {doc_id} - {filename}\n\nRelevance: {relevance}\n\nTop evidence:\n{snippets}".format(
            doc_id=item["doc_id"],
            filename=item["filename"],
            relevance=item["relevance"],
            snippets="\n".join(f"- {snippet['text']}" for snippet in item["snippets"][:4]) or "- No high-scoring evidence sentence extracted.",
        )
        for item in analyses
    )

    report = f"""# Local Qwen Analysis: Metaverse, Cryptocurrency, and Financial Crime

**Research question:** {QUESTION}

**Cost and privacy boundary:** This run used local Ollama/Qwen only. It did not use paid API calls and did not run MiroFish's Zep Cloud graph-building stage.

**Corpus:** `{INPUT_FILE}`

**Corpus size:** {aggregate_stats['input_size_bytes']:,} bytes across {aggregate_stats['document_count']} parsed documents, with {aggregate_stats['total_extracted_words_reported']:,} reported extracted words.

**Generated:** {dt.datetime.now().isoformat(timespec='seconds')}

## Final Synthesis

{final_synthesis}

## Aggregate Evidence Profile

```json
{json.dumps(aggregate_stats, ensure_ascii=False, indent=2)}
```

## Qwen Batch Summaries

{batch_summary_md}

## Document Evidence Appendix

{doc_evidence_appendix}
"""
    report_path = output_dir / "complete_analysis_report.md"
    report_path.write_text(report, encoding="utf-8")

    print(json.dumps({
        "output_dir": str(output_dir),
        "report_path": str(report_path),
        "document_count": len(analyses),
        "batch_count": len(batches),
        "manifest": str(output_dir / "manifest.json"),
        "evidence_table": str(output_dir / "document_evidence_table.csv"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
