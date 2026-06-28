# Full Code Listing
This file contains the complete scripts used to produce the local/free analysis outputs.

## code/01_local_qwen_metaverse_fincrime_analysis.py
Purpose: Parses the 4.28 MB extracted text corpus, computes evidence counts, runs local qwen2.5:7b through Ollama, and writes the first complete analysis report.

```python
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

```

## code/02_write_enhanced_metaverse_fincrime_report.py
Purpose: Uses the manifest and document evidence table to produce the enhanced journal-facing analysis report.

```python
import csv
import json
from pathlib import Path


OUT_DIR = Path(
    r"C:\Users\mtiwar05\OneDrive - Charles Sturt University\CSU\Metaverse and Cryptocurrencies\Analysis\Codex\Results\Round 5\mirofish_local_qwen_free_analysis_20260527-112059"
)
manifest = json.loads((OUT_DIR / "manifest.json").read_text(encoding="utf-8"))
with (OUT_DIR / "document_evidence_table.csv").open("r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))


def evidence_score(row):
    fields = [
        "metaverse_platform_features",
        "crypto_ecosystem_features",
        "financial_crime_opportunities",
        "modelling_analysis_intervention",
    ]
    return sum(int(row.get(field) or 0) for field in fields)


top_rows = sorted(rows, key=evidence_score, reverse=True)[:15]
top_doc_table = "\n".join(
    "| {doc_id} | {filename} | {relevance} | {score} |".format(
        doc_id=row["doc_id"],
        filename=row["filename"].replace("|", "\\|"),
        relevance=row["relevance"],
        score=evidence_score(row),
    )
    for row in top_rows
)

primary_rows = [row for row in rows if row["relevance"].startswith("primary")]
primary_doc_list = "\n".join(
    f"- **{row['doc_id']}**: {row['filename']}."
    for row in primary_rows
)

report = f"""# Enhanced Complete Analysis: Metaverse, Cryptocurrency Ecosystems, and Financial Crime

**Research question:** {manifest["analysis_question"]}

**Free/local boundary:** This enhanced report is based on the local run already completed with `qwen2.5:7b` through Ollama/MiroFish's local model service. It did **not** run MiroFish's Zep Cloud graph-building stage and did **not** use paid API calls.

**Corpus coverage:** {manifest["document_count"]} parsed documents, {manifest["total_extracted_words_reported"]:,} reported extracted words, source size {manifest["input_size_bytes"]:,} bytes.

**Aggregate signal counts from the local evidence pass:** metaverse/platform features = {manifest["category_totals"]["metaverse_platform_features"]:,}; crypto ecosystem features = {manifest["category_totals"]["crypto_ecosystem_features"]:,}; financial crime terms = {manifest["category_totals"]["financial_crime_opportunities"]:,}; modelling/analysis/intervention terms = {manifest["category_totals"]["modelling_analysis_intervention"]:,}.

## 1. Executive Answer

The combined features of metaverse platforms and cryptocurrency ecosystems create financial crime opportunities because they fuse three normally separate domains: immersive social interaction, programmable digital assets, and borderless value transfer. The metaverse supplies the social and economic setting: avatars, virtual land, NFTs, digital twins, in-world marketplaces, gaming economies, and persistent virtual communities. Cryptocurrency ecosystems supply the settlement rails: wallets, tokens, smart contracts, DeFi protocols, DAOs, bridges, exchanges, stablecoins, mixers, and privacy-oriented services. When these layers are combined, offenders can move from social manipulation to asset acquisition, conversion, layering, and integration without always touching a conventional financial institution until later in the cycle.

The corpus does not suggest that metaverse finance is uniquely criminal. Rather, it shows that familiar financial crime techniques gain new affordances in metaverse-crypto environments. Fraud becomes more immersive and identity-mediated; money laundering can be embedded in NFT trades, virtual real estate transfers, gaming assets, token swaps, and DeFi movements; market manipulation can exploit thin NFT markets and speculative token economies; identity theft can operate through avatar compromise, credential theft, wallet takeover, and deepfake-style deception; and regulatory arbitrage is intensified by decentralized governance and cross-jurisdictional platform participation.

The same combined architecture also creates analytical opportunities. Because metaverse and crypto transactions leave heterogeneous but linkable traces, financial crime environments can be modelled as multi-layer graphs connecting wallets, avatars, platform accounts, NFTs, smart contracts, marketplaces, exchanges, transaction flows, social interactions, and off-chain events. Intervention points therefore arise at several layers: design of platform architecture, identity and wallet onboarding, asset issuance, marketplace listing, transaction monitoring, cross-chain movement, fiat off-ramping, suspicious activity reporting, and post-event investigation.

The strongest corpus signals came from documents explicitly addressing future cryptoasset ML/TF opportunities, metaverse financial cybercrime, cryptocurrency scams, Ethereum fraud detection, NFT/accounting risk, identity security, AI-based cybersecurity, blockchain-metaverse architecture, and urban metaverse/blockchain security. The evidence base is broad, but uneven: the corpus is stronger on enabling technologies and risk concepts than on empirically verified metaverse-specific laundering cases.

## 2. Core Mechanism: Why the Combination Matters

Financial crime opportunity emerges from the interaction of platform affordances and crypto affordances. Neither layer alone fully explains the risk.

**Metaverse platform affordances** include immersive presence, avatars, digital identity, virtual ownership, virtual real estate, in-world marketplaces, gaming/social interaction, persistent environments, and interoperable digital assets. These features create plausible contexts in which value is assigned to non-physical objects and social trust is performed through avatars, communities, brands, influencers, or virtual organizations.

**Cryptocurrency ecosystem affordances** include pseudonymous wallets, programmable smart contracts, tokenized value, NFTs, DeFi liquidity, bridges, exchanges, stablecoins, decentralized governance, transaction automation, and cross-border settlement. These features reduce dependence on conventional intermediaries and make value movement faster, more divisible, more programmable, and more difficult to supervise with traditional AML models.

The interaction produces a financial-crime environment with five linked capabilities:

1. **Value creation and valuation ambiguity.** NFTs, virtual land, in-game items, tokenized access rights, and digital twins can be assigned high prices without mature valuation benchmarks. This creates opportunities for overvaluation, under-valuation, wash trading, sham sale, false provenance, or conversion of illicit funds into apparently legitimate digital assets.

2. **Identity fluidity and social deception.** Avatars, pseudonymous accounts, wallet addresses, and platform identities allow legitimate privacy but also enable impersonation, account compromise, romance/investment scams, fake expertise, fake customer support, and synthetic trust-building.

3. **Programmable movement and layering.** Smart contracts, DEXs, bridges, mixers, privacy tools, gaming economies, and DAOs can fragment transactions across assets, chains, contracts, and communities. This creates laundering-style layering that may not resemble bank-based transactions.

4. **Cross-jurisdictional and cross-platform dispersion.** Metaverse participants, platform servers, wallet providers, marketplaces, DAOs, exchanges, and fiat off-ramps may sit in different legal and supervisory regimes. This complicates attribution, evidence preservation, reporting duties, and enforcement.

5. **Data-rich but fragmented traceability.** Blockchain data can be transparent, but the relevant identity and behavioural signals are split across on-chain records, platform logs, marketplace metadata, social interactions, device/network data, and regulated exchange records. Analysis must therefore integrate multiple evidence layers.

## 3. Financial Crime Typology Matrix

| Typology | Combined metaverse-crypto mechanism | Key analytical signals | Intervention points |
|---|---|---|---|
| NFT or virtual asset laundering | Illicit funds are used to buy, mint, resell, or overvalue NFTs, avatars, virtual land, skins, access tokens, or digital twins. Price ambiguity and related-party trading can disguise source and ownership. | Repeated self-funded trades; newly created wallets; rapid resale; abnormal price jumps; thin-market assets with inflated value; counterparties sharing wallet clusters or platform metadata. | Marketplace due diligence; creator/seller verification; wash-trade detection; NFT provenance checks; beneficial-ownership prompts for high-value transactions; suspicious transaction reporting triggers. |
| Metaverse investment scams | Offenders use immersive environments, avatars, influencer-style trust, or virtual events to sell fake tokens, NFT projects, land, or DeFi opportunities. | New projects with aggressive promotion; pressure tactics; cloned brands; unusually high promised returns; sudden token launches; high complaint/social-signal volume. | Consumer warnings; platform vetting of financial promotions; scam-report channels; takedown protocols; wallet/exchange risk warnings; education at transaction confirmation. |
| Avatar/account takeover and identity fraud | Wallet credentials, avatar accounts, digital identities, or NFT ownership credentials are compromised, then used to steal assets or conduct fraud. | Login anomalies; wallet-drain patterns; sudden asset transfers after credential change; device/IP changes; phishing link exposure; high-value NFT holder targeting. | Multi-factor authentication; wallet transaction simulation; phishing detection; recovery and freeze procedures; risk-based re-authentication; secure custody options. |
| Cross-chain laundering and DeFi layering | Funds move through DEXs, bridges, privacy coins, mixers, stablecoins, lending/borrowing, liquidity pools, and token swaps to obscure origin. | Chain-hopping; mixer exposure; bridge-in/bridge-out bursts; stablecoin parking; split-and-merge flows; proximity to high-risk contracts; no economic rationale for complex routing. | Cross-chain analytics; Travel Rule compliance where applicable; DeFi risk scoring; bridge monitoring; stablecoin issuer freeze cooperation; exchange off-ramp screening. |
| Virtual real-estate or digital twin value manipulation | Virtual land, digital twins, and tokenized access rights are used as vehicles for speculative price manipulation, sham transactions, or illicit integration. | Related-party transactions; unusual land/asset price movements; rapid cycling between linked wallets; asset metadata manipulation; abnormal platform traffic tied to trades. | Valuation controls for high-value assets; marketplace transparency; audit trails; enhanced due diligence on large virtual land purchases; platform-marketplace data sharing. |
| DAO or platform-governance abuse | Decentralized governance can mask control, diffuse accountability, or move funds through treasury votes and smart contracts. | Concentrated token voting; coordinated wallet clusters; treasury outflows to new addresses; anonymous administrators; proposals benefiting related wallets. | DAO treasury transparency; governance risk analytics; conflict-of-interest disclosures; multisig controls; smart contract audits. |
| Money mule and grey-economy activity | Users are recruited to receive, move, cash out, or trade assets across metaverse platforms and crypto rails. | Small repeated deposits; novice accounts interacting with complex protocols; rapid off-ramp after receipt; links to scam clusters; inconsistent user profile and transaction sophistication. | User education; mule-risk scoring; off-ramp due diligence; exchange-platform referrals; behavioural anomaly detection. |
| Sanctions/terrorist financing risk | Pseudonymous value transfer, cross-border access, stablecoins, privacy tools, and decentralized services may be used to evade controls. | Sanctioned-wallet exposure; geographic/IP inconsistencies; privacy tools; small-value test transactions; fundraising narratives; links to high-risk services. | Sanctions screening; wallet risk scoring; stablecoin controls; platform moderation; law-enforcement intelligence sharing. |

## 4. Modelling and Analytical Framework

A useful model for this environment should not treat the metaverse as merely a website, or cryptocurrency as merely a payment method. The crime opportunity sits in a **multi-layer socio-technical graph**.

### 4.1 Layers of the Model

1. **Identity layer:** avatars, platform accounts, wallet addresses, verified identities, creator identities, organization accounts, device fingerprints, and linked social profiles.
2. **Asset layer:** NFTs, tokens, virtual land, in-game items, access credentials, digital twins, smart-contract rights, and stablecoins.
3. **Transaction layer:** wallet transfers, marketplace purchases, mints, burns, swaps, bridge events, DeFi lending/borrowing, exchange deposits, off-ramp withdrawals, and treasury movements.
4. **Platform interaction layer:** chats, events, social ties, guilds, DAO votes, seller-buyer interactions, marketplace listings, dispute records, reports, and moderation signals.
5. **Risk and control layer:** KYC/KYB status, sanctions exposure, smart-contract audit status, marketplace risk scores, complaint histories, scam labels, and law-enforcement flags.

The core analytical task is entity resolution across these layers. A wallet address alone is not enough; neither is an avatar name. The useful object is a linked risk graph that can say: this avatar, controlled by this account, interacted with these wallets, promoted this asset, traded with these counterparties, touched these contracts, and eventually off-ramped through these services.

### 4.2 Analytical Features

Important features include:

- **Temporal features:** bursty trading, rapid resale, short holding periods, repeated activity after new account creation, transaction timing around promotional events.
- **Network features:** fan-in/fan-out, circular trading, shared counterparties, wallet clustering, distance to known illicit addresses, bridge/mixer exposure, centrality within scam clusters.
- **Asset features:** abnormal price appreciation, illiquid asset resale, repeated sale between small wallet sets, metadata changes, cloned content, suspicious royalty structures.
- **Behavioural features:** mismatch between user sophistication and transaction complexity, repeated failed security attempts, social-engineering interactions, platform complaints.
- **Governance features:** DAO proposal concentration, treasury outflows, administrator anonymity, repeated proposals benefiting linked wallets.
- **Regulatory features:** KYC gaps, use of high-risk jurisdictions, exchange/off-ramp exposure, sanctions indicators, missing beneficial-owner information.

### 4.3 Suitable Methods

The corpus supports a mixed-method analytical approach:

- **Typology rules** for known behaviours: mixer exposure, rapid self-trading, suspicious NFT overvaluation, bridge layering, high-risk off-ramp behaviour.
- **Graph analytics** to identify clusters, circular flows, counterparties, mule networks, marketplace collusion, and connections between avatars and wallets.
- **Machine learning and anomaly detection** for abnormal transaction structures, wallet behaviour, NFT pricing, phishing patterns, and account-takeover signals.
- **NLP and social-signal analysis** for scam promotion, fake project language, investor pressure, complaint clustering, impersonation, and suspicious community narratives.
- **Smart-contract analysis** for vulnerabilities, hidden privileges, treasury-drain functions, proxy contracts, minting abuse, and unaudited DeFi interactions.
- **Human-in-the-loop review** for high-value assets, ambiguous valuation, legal thresholds, user privacy, and enforcement decisions.

## 5. Intervention Points Across the Lifecycle

The strongest intervention strategy is layered. No single control can solve metaverse-crypto financial crime because the risk moves between identity, platform behaviour, blockchain transactions, marketplace activity, and fiat conversion.

### 5.1 Design and Governance Stage

At platform design, controls should include accountable identity architecture, privacy-preserving but auditable logs, smart-contract auditing, asset provenance standards, dispute mechanisms, high-risk product review, and governance transparency. This is where platform providers can make later investigations possible without eliminating user privacy.

### 5.2 Onboarding Stage

Controls include risk-based KYC/KYB for creators, sellers, high-value traders, financial-service providers, land sellers, and custodial services. Low-risk users may not require intrusive checks, but high-risk activity should trigger verification. Wallet screening at onboarding can identify sanctioned or previously illicit addresses.

### 5.3 Asset Issuance and Listing Stage

NFTs, virtual land, digital twins, and tokenized project assets should be screened for provenance, intellectual property concerns, cloned content, suspicious metadata, and unrealistic pricing. Creator verification and marketplace-level listing controls can reduce scam launches and laundering through self-issued assets.

### 5.4 Transaction and Marketplace Stage

Real-time monitoring should detect rapid resale, circular trading, split-and-merge patterns, bridge/mixer interaction, repeated stablecoin conversions, and price manipulation. For high-risk transactions, platforms can introduce friction: warnings, delayed settlement, enhanced due diligence, or manual review.

### 5.5 Cross-Chain and DeFi Stage

Bridges, DEXs, DeFi pools, and privacy-enhancing services are critical layering points. Intervention does not always mean blocking; it can mean risk scoring, alerting, suspicious activity reporting, enhanced due diligence at connected centralized services, stablecoin issuer cooperation, and preservation of transaction evidence.

### 5.6 Off-Ramp Stage

Fiat off-ramps remain one of the most important AML points. Exchanges, payment processors, banks, and OTC desks should integrate metaverse-specific risk indicators: NFT wash-trade exposure, platform scam reports, virtual land overvaluation, avatar-account compromise, and DAO treasury risk.

### 5.7 Post-Event Investigation

Post-event intervention requires preserving platform logs, chat records, transaction hashes, wallet clusters, smart-contract addresses, asset metadata, marketplace histories, and user complaints. Investigators should reconstruct the pathway from social contact to asset transfer to crypto layering to off-ramp.

## 6. Indicators and Red Flags

High-value signals include:

- New wallet or new platform account rapidly purchasing high-value NFTs or virtual land.
- Same or related wallets repeatedly buying and selling the same NFT or virtual asset.
- NFT sale price substantially inconsistent with comparable assets or prior transaction history.
- Proceeds from scams, ransomware, theft, or phishing moving into NFTs, virtual land, gaming assets, or metaverse tokens.
- Chain-hopping, bridge use, mixer exposure, privacy-coin interaction, or rapid stablecoin conversion after metaverse asset sale.
- High-value asset holder receiving phishing links, impersonated support messages, or suspicious wallet-connection prompts.
- DAO treasury transfers to recently created or poorly attributed addresses.
- Platform account behaviour inconsistent with wallet sophistication.
- Multiple victims reporting the same avatar, seller, project, virtual event, or metaverse investment scheme.
- Sudden promotional bursts around a token, NFT mint, land sale, or DeFi opportunity, followed by liquidity extraction.

## 7. Evidence Base from the Corpus

The corpus-wide evidence pass found {manifest["relevance_counts"].get("primary financial-crime/crypto evidence", 0)} documents classified as primary financial-crime/crypto evidence and {manifest["relevance_counts"].get("highly relevant platform/security evidence", 0)} documents classified as highly relevant platform/security evidence.

Primary financial-crime/crypto evidence documents:

{primary_doc_list}

Top documents by combined evidence score:

| DOC_ID | File | Relevance | Evidence score |
|---|---|---|---|
{top_doc_table}

The strongest financial-crime anchors were the cryptoasset ML/TF scoping article, financial cybercrime in Islamic finance metaverse, cryptocurrency scams/grey economy, accounting risks around NFTs, Ethereum fraud detection, and broader cryptocurrency market/regulation work. The strongest platform-security anchors were the AI cybersecurity, blockchain-metaverse taxonomy, identity-security, NFT, urban-metaverse, and trust/blockchain articles.

## 8. Implications

### AML/CTF

AML/CTF programs need to move from institution-only monitoring to ecosystem monitoring. Risk indicators must capture wallet behaviour, platform behaviour, NFT/virtual asset behaviour, and off-ramp behaviour. Existing controls such as KYC, sanctions screening, transaction monitoring, and suspicious matter reporting remain relevant, but they need metaverse-specific typologies and data-sharing arrangements.

### Regulation

Regulation should clarify who is responsible when financial activity occurs across platform operators, NFT marketplaces, wallet providers, exchanges, DAO structures, and smart contracts. The main gap is not only whether assets are regulated, but where supervision attaches in a transaction chain that crosses social platform, marketplace, blockchain, and fiat systems.

### Platforms and Marketplaces

Platforms cannot treat financial crime as only an exchange problem. If platforms host asset issuance, land sales, branded NFTs, financial promotions, or wallet-linked activity, they become part of the risk environment. They need fraud reporting, provenance controls, suspicious-asset review, moderation links to wallet risk, and escalation pathways.

### Exchanges and Fiat Off-Ramps

Exchanges are still vital because many offenders eventually need liquidity. Off-ramps should integrate metaverse-specific risk data: NFT wash trading, high-risk platform reports, suspicious virtual land trades, and wallets linked to scam clusters.

### Law Enforcement and FIUs

Investigators need the ability to reconstruct both the social and transactional chain. A purely on-chain analysis may miss avatar impersonation, fake events, and victim grooming; a purely platform-based analysis may miss bridge, mixer, DeFi, and off-ramp layering.

## 9. Research Gaps and Cautions

The evidence base is conceptually rich but still emergent. Many documents discuss risks, architectures, and countermeasures, while fewer provide detailed empirical cases of actual metaverse-specific laundering pathways. The local analysis also used extracted text with OCR/noise artefacts, and the evidence pass used keyword-based retrieval before local Qwen synthesis. Therefore, the report is best treated as a robust thematic and conceptual analysis rather than a statistical measurement of crime prevalence.

Further research should develop validated typologies, case datasets, cross-chain/pathway reconstructions, marketplace manipulation metrics, avatar-wallet entity resolution methods, and privacy-preserving data-sharing mechanisms between platforms, exchanges, FIUs, and law enforcement.

## 10. Conclusion

Metaverse platforms and cryptocurrency ecosystems generate financial crime opportunities by combining immersive social engineering, ambiguous digital asset valuation, pseudonymous identity, programmable value transfer, decentralized governance, and cross-border/cross-chain liquidity. These same features also create intervention opportunities if they are modelled as a multi-layer graph linking identity, asset, transaction, behaviour, governance, and regulatory data. The most promising intervention points are not concentrated at one gate; they are distributed across platform design, onboarding, asset issuance, marketplace behaviour, transaction monitoring, DeFi/bridge movement, fiat off-ramping, and post-event investigation.

The practical answer to the research question is therefore: metaverse-crypto environments expand financial crime opportunity by creating new objects of value and new routes for deception, conversion, layering, and integration; they can be analysed by joining platform and blockchain evidence; and they can be disrupted through risk-based controls placed at the moments where identity, value, transaction, and liquidity intersect.
"""

(OUT_DIR / "enhanced_complete_analysis_report.md").write_text(report, encoding="utf-8")
print(str(OUT_DIR / "enhanced_complete_analysis_report.md"))

```

## code/03_markdown_to_docx_simple.py
Purpose: Converts the enhanced markdown report into a Word document.

```python
from pathlib import Path

from docx import Document
from docx.shared import Pt


SOURCE = Path(
    r"C:\Users\mtiwar05\OneDrive - Charles Sturt University\CSU\Metaverse and Cryptocurrencies\Analysis\Codex\Results\Round 5\mirofish_local_qwen_free_analysis_20260527-112059\enhanced_complete_analysis_report.md"
)
TARGET = SOURCE.with_suffix(".docx")


def clean_inline(text):
    return text.replace("**", "").replace("`", "")


doc = Document()
styles = doc.styles
styles["Normal"].font.name = "Aptos"
styles["Normal"].font.size = Pt(10.5)

lines = SOURCE.read_text(encoding="utf-8").splitlines()
i = 0
while i < len(lines):
    line = lines[i].rstrip()
    if not line:
        i += 1
        continue

    if line.startswith("|") and i + 1 < len(lines) and lines[i + 1].startswith("|"):
        table_lines = []
        while i < len(lines) and lines[i].startswith("|"):
            table_lines.append(lines[i])
            i += 1
        rows = []
        for idx, table_line in enumerate(table_lines):
            cells = [clean_inline(cell.strip()) for cell in table_line.strip("|").split("|")]
            if idx == 1 and all(set(cell.replace(":", "").replace("-", "").strip()) == set() for cell in cells):
                continue
            rows.append(cells)
        if rows:
            table = doc.add_table(rows=len(rows), cols=max(len(row) for row in rows))
            table.style = "Table Grid"
            for r, row in enumerate(rows):
                for c, cell in enumerate(row):
                    table.cell(r, c).text = cell
        continue

    if line.startswith("# "):
        doc.add_heading(clean_inline(line[2:]), level=1)
    elif line.startswith("## "):
        doc.add_heading(clean_inline(line[3:]), level=2)
    elif line.startswith("### "):
        doc.add_heading(clean_inline(line[4:]), level=3)
    elif line.startswith("- "):
        doc.add_paragraph(clean_inline(line[2:]), style="List Bullet")
    elif line and line[0].isdigit() and ". " in line[:5]:
        doc.add_paragraph(clean_inline(line.split(". ", 1)[1]), style="List Number")
    else:
        doc.add_paragraph(clean_inline(line))
    i += 1

doc.save(TARGET)
print(TARGET)

```

## code/04_write_topic_model_intervention_focus.py
Purpose: Builds the topic-modelling intervention focus report and the Mermaid/SVG framework figure.

```python
from pathlib import Path

from docx import Document
from docx.shared import Pt


OUT_DIR = Path(
    r"C:\Users\mtiwar05\OneDrive - Charles Sturt University\CSU\Metaverse and Cryptocurrencies\Analysis\Codex\Results\Round 5\mirofish_local_qwen_free_analysis_20260527-112059"
)

md_path = OUT_DIR / "topic_model_emerging_threats_modelling_intervention_focus.md"
docx_path = OUT_DIR / "topic_model_emerging_threats_modelling_intervention_focus.docx"
svg_path = OUT_DIR / "topic_model_threat_intervention_framework.svg"
mmd_path = OUT_DIR / "topic_model_threat_intervention_framework.mmd"

report = """# Topic-Modelling Focus: Emerging Threats, Modelling, Analysis, and Intervention Points

## Reframed Contribution

The Round 5 topic modelling should be interpreted as more than a thematic map of metaverse and cryptocurrency scholarship. It identifies **emerging threat environments** at the intersection of metaverse platforms and cryptocurrency ecosystems. The strongest contribution of the analysis is therefore not simply that metaverse and crypto features create opportunities for financial crime, but that the topic structure helps organise how those opportunities can be **modelled, analysed, and converted into intervention points**.

This reframing keeps the analysis aligned with the research question:

> How do the combined features of metaverse platforms and cryptocurrency ecosystems generate new money laundering and other financial crime opportunities, and subsequently help model, analyse, and identify intervention points within these emerging financial crime environments?

Under this framing, the topic model performs three analytical functions. First, it identifies the main domains in which emerging threats cluster. Second, it shows which domains are connected across technical, financial, governance, identity, and security layers. Third, it provides a structure for deciding where interventions should be placed.

## Topic-Modelling Basis

The Round 5 LDA model retained **seven topics** using a coherence-first decision rule. The corpus comprised **59 PDFs**, **545,779 extracted words**, **247,995 cleaned tokens**, and **332 modelling/scoring chunks**. The selected model was **K = 7**, with c_v coherence of **0.418574**, perplexity of **275.029468**, and log-likelihood bound of **-1,596,070.22**.

The seven topics are best read as a layered map of emerging financial crime environments:

| Topic | Topic label | Prevalence | Dominant PDFs | Threat-environment interpretation |
|---|---:|---:|---:|---|
| T6 | Crypto finance, DeFi, scams, and grey-economy risks | 19.17% | 13 | Core money-laundering, scam, grey-economy, and illicit-finance environment. |
| T2 | Avatar privacy, cyberattack detection, and metaverse security | 18.53% | 10 | Identity, avatar, behavioural, cyberattack, and security-monitoring environment. |
| T1 | Blockchain-based metaverse governance, ownership, and token infrastructure | 16.30% | 8 | Governance, ownership, token infrastructure, trust, and protocol environment. |
| T7 | Cryptographic access control, authentication, and encryption protocols | 13.64% | 9 | Authentication, encryption, access-control, transfer-transaction, and privacy-preserving-control environment. |
| T5 | Blockchain gaming, NFT markets, and digital-property law | 13.37% | 7 | NFT market, gaming economy, jurisdiction, property, volatility, and Sybil-wallet environment. |
| T3 | Cryptocurrency networks, wallets, exchanges, and regulatory risk | 9.65% | 7 | Wallet, exchange, Bitcoin-network, anonymity, illicit-finance, Tornado Cash, and regulatory-risk environment. |
| T4 | Digital payments, privacy policy, trust, and fraud detection | 9.34% | 5 | Payment, privacy-policy, off-chain transaction, fraud-detection, gas-fee, and Sybil-attack environment. |

## Emerging Threat Environments Identified by the Topic Model

### 1. Crypto Finance, DeFi, Scams, and Grey-Economy Risks

T6 is the largest topic and is the clearest direct anchor for money laundering and financial crime. It identifies the threat environment in which cryptocurrency, digital currency, DeFi, scams, social media, and grey-economy activity intersect. This topic indicates that metaverse financial crime should not be modelled only as a technical cybersecurity issue; it also involves fraud scripts, social influence, speculative markets, informal economies, and offender adaptation.

For modelling, this topic points to scam typology construction, wallet-flow analysis, fraud network mapping, and social-signal monitoring. For intervention, it points to scam warnings, suspicious wallet clustering, off-ramp due diligence, platform moderation, and cross-platform reporting of fraudulent campaigns.

### 2. Avatar Privacy, Cyberattack Detection, and Metaverse Security

T2 identifies a second threat environment around avatars, attacks, prediction, detection, cybersecurity, authentication, immersive behaviour, nodes, and behavioural patterns. This topic shifts the analysis from crypto transactions alone to identity-mediated financial crime. In metaverse settings, avatars are not just visual representations; they can become trust-bearing, asset-holding, social-engineering, and authentication targets.

For modelling, T2 supports avatar-wallet-account linkage, behavioural anomaly detection, cyberattack prediction, credential-compromise analysis, and identity-risk scoring. For intervention, it points to risk-based re-authentication, phishing detection, wallet-drain alerts, avatar impersonation controls, behavioural monitoring, and identity-recovery procedures.

### 3. Blockchain Governance, Ownership, and Token Infrastructure

T1 captures the governance and infrastructure layer: trust, governance, ownership, blockchain networks, tokens, swaps, infrastructure, and protocols. This threat environment matters because financial crime risk often emerges from control points embedded in protocols, DAOs, token issuance, asset ownership systems, and cross-platform infrastructure.

For modelling, T1 supports governance-risk graphs, smart-contract dependency mapping, ownership-chain analysis, DAO treasury monitoring, and token-infrastructure risk scoring. For intervention, it points to governance transparency, smart-contract audits, multisig controls, project disclosure, treasury-monitoring triggers, and accountability controls for token issuers and virtual organisations.

### 4. Cryptographic Access Control, Authentication, and Encryption Protocols

T7 shows that intervention cannot rely only on post-transaction detection. Access control, authentication protocols, cryptographic key management, privacy-preserving technology, and on-chain transfer mechanisms form a preventive control environment. The threat is not only misuse of assets after acquisition, but also compromise of access rights, keys, credentials, and transfer permissions.

For modelling, T7 supports authentication-failure analysis, key-management risk mapping, access-control policy modelling, credential-compromise pathways, and secure-transfer process modelling. For intervention, it points to multi-factor authentication, hardware or custodial safeguards for high-value assets, smart-contract permission review, recovery protocols, and privacy-preserving compliance mechanisms.

### 5. Blockchain Gaming, NFT Markets, and Digital-Property Law

T5 maps a threat environment around gaming, NFTs, jurisdiction, property, intellectual property, volatility, and Sybil wallets. This is where criminal opportunity is linked to asset valuation, market opacity, digital-property rights, jurisdictional uncertainty, and gaming economies. NFT and virtual-property markets create plausible mechanisms for overvaluation, wash trading, sham sale, account farming, and illicit integration.

For modelling, T5 supports NFT wash-trading detection, virtual-property valuation anomaly analysis, Sybil-wallet identification, marketplace manipulation metrics, and jurisdictional-risk mapping. For intervention, it points to marketplace surveillance, provenance standards, high-value transaction checks, related-wallet detection, intellectual-property review, and stronger reporting protocols for suspicious virtual-asset trades.

### 6. Cryptocurrency Networks, Wallets, Exchanges, and Regulatory Risk

T3 identifies the regulated and semi-regulated crypto-financial interface: wallets, exchanges, Bitcoin networks, anonymity/privacy, illicit finance, consumer protection, addresses, and Tornado Cash. This topic is critical because many metaverse-crypto crimes eventually require liquidity, exchange access, stablecoin movement, or conversion into fiat.

For modelling, T3 supports wallet-cluster analysis, exchange interaction mapping, exposure to high-risk services, mixer/bridge/pathway tracing, and regulatory-risk scoring. For intervention, it points to exchange due diligence, wallet screening, sanctions and mixer exposure alerts, Travel Rule-style data sharing where applicable, and off-ramp review.

### 7. Digital Payments, Privacy Policy, Trust, and Fraud Detection

T4 isolates the payment and fraud-detection layer: privacy policy, digital payments, fraud detection, gas fees, data flows, off-chain transactions, trust management, and Sybil attack. This topic shows that intervention must consider both on-chain and off-chain environments. Fraud may be executed through off-chain communications and platform-level trust cues, while value transfer occurs on-chain or through connected payment systems.

For modelling, T4 supports fraud-detection models that combine transaction metadata, platform logs, privacy-policy exposure, payment-flow data, and Sybil indicators. For intervention, it points to payment monitoring, transparent privacy policies, platform-level fraud reporting, off-chain/on-chain data linkage, and Sybil-resistance mechanisms.

## Modelling Framework

The topic model supports a **multi-layer threat-modelling framework**. Each LDA topic can be treated as a layer or module in an emerging financial crime environment.

| Model layer | Topic anchor | Main entities | Main relationships | Analytical purpose |
|---|---|---|---|---|
| Social-deception layer | T6, T2 | avatars, victims, promoters, communities, social media accounts | influences, impersonates, recruits, deceives | Identify scams, grooming, trust manipulation, and victim pathways. |
| Identity-access layer | T2, T7 | avatars, wallets, keys, credentials, devices, authentication events | controls, compromises, authenticates, transfers | Detect account takeover, identity theft, wallet compromise, and credential abuse. |
| Asset-market layer | T5, T1 | NFTs, virtual land, game assets, tokens, smart contracts, marketplaces | mints, lists, buys, sells, swaps, owns | Detect wash trading, overvaluation, sham sale, suspicious asset cycling, and market manipulation. |
| Transaction-flow layer | T3, T4, T6 | wallets, exchanges, bridges, mixers, DeFi pools, stablecoins | sends, receives, swaps, bridges, off-ramps | Trace laundering, layering, chain-hopping, mixer exposure, and fiat conversion. |
| Governance-control layer | T1, T7 | DAOs, protocols, multisig wallets, platform operators, regulators | governs, audits, approves, enforces | Identify weak governance, treasury risk, protocol abuse, and points of accountability. |
| Detection-intervention layer | T2, T4, T7 | risk models, alerts, reports, compliance controls, law-enforcement actions | flags, blocks, escalates, investigates | Convert signals into prevention, monitoring, reporting, and enforcement actions. |

This framework helps avoid a narrow reading of financial crime as only transaction movement. In metaverse-cryptocurrency environments, offending can begin in social interaction, move through identity compromise or asset promotion, become encoded in virtual asset transactions, pass through crypto infrastructure, and only later appear at an exchange or fiat off-ramp.

## Analytical Indicators by Threat Environment

| Threat environment | Indicators for analysis |
|---|---|
| Scam and grey-economy finance | repeated promotional activity, high-return claims, victim reports, wallet clusters linked to scam campaigns, rapid movement to exchanges or bridges. |
| Avatar and identity abuse | sudden device or login changes, high-value asset transfers after credential reset, avatar impersonation, wallet-drain patterns, phishing-link exposure. |
| Governance and token infrastructure | concentrated DAO voting, treasury transfers to new wallets, unaudited smart contracts, opaque project control, suspicious token allocation. |
| Authentication and access control | failed authentication bursts, key compromise events, abnormal permission grants, risky smart-contract approvals, unusual transfer permissions. |
| NFT markets and virtual property | self-funded trades, circular NFT movement, abnormal price spikes, related-wallet counterparties, suspicious metadata/provenance, Sybil wallet behaviour. |
| Wallets, exchanges, and regulatory risk | mixer or Tornado Cash exposure, bridge chains, rapid stablecoin conversion, high-risk jurisdiction signals, exchange off-ramp attempts after suspicious NFT/DeFi activity. |
| Digital payments and fraud detection | off-chain payment promises, privacy-policy gaps, Sybil attack patterns, gas-fee anomalies, suspicious off-chain/on-chain timing relationships. |

## Intervention Points

The intervention model should follow the lifecycle of emerging metaverse-crypto financial crime:

1. **Platform and protocol design:** require auditability, suspicious activity logging, secure smart-contract design, provenance standards, and privacy-preserving compliance controls.
2. **Onboarding and identity:** apply risk-based verification to high-value creators, sellers, financial-service operators, DAO controllers, and repeat high-risk traders.
3. **Asset issuance and listing:** screen NFT collections, virtual land, token launches, and digital twins for provenance, suspicious valuation, cloned content, and hidden control.
4. **Market and transaction activity:** detect wash trading, circular wallet flows, bridge layering, mixer exposure, Sybil wallets, rapid resale, abnormal pricing, and asset cycling.
5. **Social and behavioural monitoring:** monitor scam campaigns, fake events, impersonation, account takeover, phishing, and influencer-style financial promotions.
6. **Cross-chain and DeFi movement:** apply risk scoring to bridges, DEXs, liquidity pools, stablecoin conversions, and high-risk services.
7. **Exchange and fiat off-ramp:** integrate metaverse-specific risk indicators into KYC, transaction monitoring, enhanced due diligence, and suspicious matter reporting.
8. **Post-event investigation:** preserve wallet histories, asset metadata, marketplace logs, avatar-account records, chat evidence, smart-contract addresses, and off-ramp data.

## Revised Manuscript Argument

The topic modelling indicates that emerging financial crime risks at the metaverse-cryptocurrency intersection are not confined to a single technological domain. Rather, they form a multi-layered threat environment in which crypto-finance and grey-economy risks (T6), avatar privacy and cyberattack detection (T2), blockchain governance and token infrastructure (T1), cryptographic access control (T7), NFT markets and digital-property law (T5), wallet/exchange regulatory risk (T3), and digital-payment fraud detection (T4) operate as interdependent layers.

This layered topic structure helps move the analysis from description to modelling. Each topic identifies a class of entities, relationships, behavioural indicators, and control points. Together, the topics support a graph-based and lifecycle-based model of emerging financial crime environments. This model links avatars, wallets, NFTs, virtual land, smart contracts, exchanges, DAOs, bridges, platform accounts, social interactions, and regulatory controls. It also helps identify intervention points before, during, and after suspicious activity: secure-by-design architecture, risk-based onboarding, asset-listing controls, transaction monitoring, behavioural anomaly detection, cross-chain analytics, off-ramp due diligence, and evidence-preserving investigation.

The main contribution is therefore that topic modelling identifies the structure of emerging threats and provides a basis for modelling how money laundering and related financial crimes can be detected and disrupted in metaverse-cryptocurrency ecosystems.
"""

mermaid = """flowchart LR
    T6["T6 Crypto finance, DeFi, scams, grey-economy risks"] --> M["Emerging metaverse-crypto financial crime environment"]
    T2["T2 Avatar privacy, cyberattack detection, security"] --> M
    T1["T1 Governance, ownership, token infrastructure"] --> M
    T7["T7 Access control, authentication, encryption"] --> M
    T5["T5 Gaming, NFT markets, digital-property law"] --> M
    T3["T3 Wallets, exchanges, regulatory risk"] --> M
    T4["T4 Payments, privacy policy, fraud detection"] --> M
    M --> A["Model: multi-layer graph of avatars, wallets, assets, contracts, platforms, exchanges"]
    A --> B["Analyse: typologies, anomaly signals, entity links, transaction paths, behavioural patterns"]
    B --> C["Intervene: design controls, onboarding, marketplace review, transaction monitoring, cross-chain analytics, off-ramp due diligence, investigation"]
"""

svg = """<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="880" viewBox="0 0 1400 880">
  <style>
    .topic { fill:#f7f7f7; stroke:#333; stroke-width:1.4; rx:8; }
    .core { fill:#fff3cd; stroke:#9a6b00; stroke-width:2; rx:8; }
    .stage { fill:#e9f5ff; stroke:#185a8d; stroke-width:1.8; rx:8; }
    .label { font-family:Arial, sans-serif; font-size:18px; fill:#111; }
    .small { font-family:Arial, sans-serif; font-size:15px; fill:#222; }
    .title { font-family:Arial, sans-serif; font-size:26px; font-weight:bold; fill:#111; }
    .arrow { stroke:#333; stroke-width:1.6; marker-end:url(#arrow); }
  </style>
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#333"/>
    </marker>
  </defs>
  <text x="70" y="50" class="title">Topic Model to Threat Modelling and Intervention Framework</text>

  <rect x="60" y="90" width="370" height="70" class="topic"/><text x="78" y="120" class="label">T6 Crypto finance, DeFi, scams</text><text x="78" y="145" class="small">Grey economy, ML/TF, scam pathways</text>
  <rect x="60" y="180" width="370" height="70" class="topic"/><text x="78" y="210" class="label">T2 Avatar privacy and cyberattack</text><text x="78" y="235" class="small">Identity, behaviour, detection, security</text>
  <rect x="60" y="270" width="370" height="70" class="topic"/><text x="78" y="300" class="label">T1 Governance and token infrastructure</text><text x="78" y="325" class="small">Ownership, protocols, trust, swaps</text>
  <rect x="60" y="360" width="370" height="70" class="topic"/><text x="78" y="390" class="label">T7 Access control and authentication</text><text x="78" y="415" class="small">Keys, encryption, permissions, on-chain transfer</text>
  <rect x="60" y="450" width="370" height="70" class="topic"/><text x="78" y="480" class="label">T5 Gaming, NFTs, digital property</text><text x="78" y="505" class="small">Markets, jurisdiction, volatility, Sybil wallets</text>
  <rect x="60" y="540" width="370" height="70" class="topic"/><text x="78" y="570" class="label">T3 Wallets, exchanges, regulation</text><text x="78" y="595" class="small">Anonymity, illicit finance, off-ramp risk</text>
  <rect x="60" y="630" width="370" height="70" class="topic"/><text x="78" y="660" class="label">T4 Payments, privacy, fraud detection</text><text x="78" y="685" class="small">Off-chain transactions, trust, Sybil attacks</text>

  <rect x="520" y="300" width="360" height="150" class="core"/>
  <text x="545" y="335" class="label">Emerging metaverse-crypto</text>
  <text x="545" y="362" class="label">financial crime environment</text>
  <text x="545" y="395" class="small">A layered socio-technical setting where</text>
  <text x="545" y="417" class="small">identity, assets, transactions, governance,</text>
  <text x="545" y="439" class="small">and controls interact.</text>

  <rect x="990" y="170" width="320" height="100" class="stage"/>
  <text x="1015" y="205" class="label">Model</text>
  <text x="1015" y="233" class="small">Graph avatars, wallets, assets,</text>
  <text x="1015" y="254" class="small">contracts, platforms, exchanges</text>
  <rect x="990" y="340" width="320" height="100" class="stage"/>
  <text x="1015" y="375" class="label">Analyse</text>
  <text x="1015" y="403" class="small">Typologies, anomalies, entity links,</text>
  <text x="1015" y="424" class="small">transaction paths, behaviour</text>
  <rect x="990" y="510" width="320" height="130" class="stage"/>
  <text x="1015" y="545" class="label">Intervene</text>
  <text x="1015" y="573" class="small">Design controls, onboarding, marketplace</text>
  <text x="1015" y="594" class="small">review, monitoring, cross-chain analytics,</text>
  <text x="1015" y="615" class="small">off-ramp due diligence, investigation</text>

  <line x1="430" y1="125" x2="520" y2="350" class="arrow"/>
  <line x1="430" y1="215" x2="520" y2="360" class="arrow"/>
  <line x1="430" y1="305" x2="520" y2="370" class="arrow"/>
  <line x1="430" y1="395" x2="520" y2="380" class="arrow"/>
  <line x1="430" y1="485" x2="520" y2="390" class="arrow"/>
  <line x1="430" y1="575" x2="520" y2="400" class="arrow"/>
  <line x1="430" y1="665" x2="520" y2="410" class="arrow"/>
  <line x1="880" y1="350" x2="990" y2="220" class="arrow"/>
  <line x1="880" y1="375" x2="990" y2="390" class="arrow"/>
  <line x1="880" y1="410" x2="990" y2="575" class="arrow"/>
</svg>
"""

md_path.write_text(report, encoding="utf-8")
mmd_path.write_text(mermaid, encoding="utf-8")
svg_path.write_text(svg, encoding="utf-8")

doc = Document()
doc.styles["Normal"].font.name = "Aptos"
doc.styles["Normal"].font.size = Pt(10.5)

for line in report.splitlines():
    if not line.strip():
        continue
    if line.startswith("# "):
        doc.add_heading(line[2:], level=1)
    elif line.startswith("## "):
        doc.add_heading(line[3:], level=2)
    elif line.startswith("### "):
        doc.add_heading(line[4:], level=3)
    elif line.startswith("|"):
        # Tables are retained in the markdown version; keep Word simple/readable.
        doc.add_paragraph(line)
    elif line.startswith("- "):
        doc.add_paragraph(line[2:], style="List Bullet")
    elif line[:2].isdigit() and ". " in line[:5]:
        doc.add_paragraph(line.split(". ", 1)[1], style="List Number")
    else:
        doc.add_paragraph(line.replace("**", "").replace("`", ""))

doc.save(docx_path)
print(md_path)
print(docx_path)
print(svg_path)
print(mmd_path)

```

## code/05_build_free_graph_pack.py
Purpose: Builds the fully local/free graph pack: interactive HTML, SVG graphs, JSON, CSV, GraphML, and intervention matrix.

```python
from __future__ import annotations

import csv
import html
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape


BASE_DIR = Path(
    r"C:\Users\mtiwar05\OneDrive - Charles Sturt University\CSU\Metaverse and Cryptocurrencies\Analysis\Codex\Results\Round 5\mirofish_local_qwen_free_analysis_20260527-112059"
)
EVIDENCE_CSV = BASE_DIR / "document_evidence_table.csv"
PACK_DIR = BASE_DIR / "free_full_graph_pack"


TOPICS = [
    {
        "id": "T6",
        "label": "Crypto finance, DeFi, scams, and grey-economy risks",
        "prevalence": 19.17,
        "documents": 13,
        "threats": ["TH_SCAM", "TH_WALLET", "TH_DEFI"],
    },
    {
        "id": "T2",
        "label": "Avatar privacy, cyberattack detection, and metaverse security",
        "prevalence": 18.53,
        "documents": 10,
        "threats": ["TH_IDENTITY", "TH_CYBER", "TH_PRIVACY"],
    },
    {
        "id": "T1",
        "label": "Blockchain-based metaverse governance, ownership, and token infrastructure",
        "prevalence": 16.30,
        "documents": 8,
        "threats": ["TH_GOVERNANCE", "TH_DEFI", "TH_NFT"],
    },
    {
        "id": "T7",
        "label": "Cryptographic access control, authentication, and encryption protocols",
        "prevalence": 13.64,
        "documents": 9,
        "threats": ["TH_IDENTITY", "TH_PRIVACY", "TH_CYBER"],
    },
    {
        "id": "T5",
        "label": "Blockchain gaming, NFT markets, and digital-property law",
        "prevalence": 13.37,
        "documents": 7,
        "threats": ["TH_NFT", "TH_SCAM", "TH_GOVERNANCE"],
    },
    {
        "id": "T3",
        "label": "Cryptocurrency networks, wallets, exchanges, and regulatory risk",
        "prevalence": 9.65,
        "documents": 7,
        "threats": ["TH_WALLET", "TH_DEFI", "TH_PAYMENT"],
    },
    {
        "id": "T4",
        "label": "Digital payments, privacy policy, trust, and fraud detection",
        "prevalence": 9.34,
        "documents": 5,
        "threats": ["TH_PAYMENT", "TH_PRIVACY", "TH_SCAM"],
    },
]


THREATS = [
    {
        "id": "TH_SCAM",
        "label": "Scam, fraud, and social-deception laundering opportunities",
        "keywords": [
            "fraud",
            "scam",
            "social engineering",
            "phishing",
            "cybercrime",
            "financial fraud",
            "money laundering",
            "laundering",
        ],
        "layer": "LY_OPPORTUNITY",
        "signal": "SG_SCAM",
        "interventions": ["IN_SCAM_MONITOR", "IN_EVIDENCE", "IN_MARKETPLACE"],
    },
    {
        "id": "TH_IDENTITY",
        "label": "Avatar, identity, biometric, and account takeover abuse",
        "keywords": [
            "avatar",
            "identity",
            "biometric",
            "deepfake",
            "authentication",
            "account",
            "fingerprint",
            "credential",
        ],
        "layer": "LY_IDENTITY",
        "signal": "SG_AVATAR",
        "interventions": ["IN_ONBOARDING", "IN_ACCESS", "IN_EVIDENCE"],
    },
    {
        "id": "TH_NFT",
        "label": "NFT, gaming, and virtual-property value manipulation",
        "keywords": [
            "nft",
            "non-fungible",
            "gaming",
            "game",
            "digital asset",
            "virtual asset",
            "property",
            "marketplace",
            "wash",
        ],
        "layer": "LY_ASSET",
        "signal": "SG_NFT",
        "interventions": ["IN_PROVENANCE", "IN_MARKETPLACE", "IN_VALUATION"],
    },
    {
        "id": "TH_WALLET",
        "label": "Wallet, exchange, off-ramp, and cross-chain laundering exposure",
        "keywords": [
            "wallet",
            "exchange",
            "bitcoin",
            "cryptocurrency",
            "crypto",
            "transaction",
            "off-ramp",
            "mixer",
            "bridge",
            "address",
        ],
        "layer": "LY_TRANSACTION",
        "signal": "SG_WALLET",
        "interventions": ["IN_CHAIN_ANALYTICS", "IN_OFFRAMP", "IN_EVIDENCE"],
    },
    {
        "id": "TH_DEFI",
        "label": "DeFi, smart-contract, DAO, and governance-control misuse",
        "keywords": [
            "defi",
            "decentralized",
            "smart contract",
            "dao",
            "protocol",
            "governance",
            "token",
            "treasury",
        ],
        "layer": "LY_GOVERNANCE",
        "signal": "SG_CONTRACT",
        "interventions": ["IN_GOVERNANCE_AUDIT", "IN_CHAIN_ANALYTICS", "IN_PROVENANCE"],
    },
    {
        "id": "TH_PRIVACY",
        "label": "Privacy, data protection, and traceability gaps",
        "keywords": [
            "privacy",
            "data protection",
            "personal data",
            "confidential",
            "encryption",
            "anonymous",
            "anonymity",
            "traceability",
        ],
        "layer": "LY_IDENTITY",
        "signal": "SG_PRIVACY",
        "interventions": ["IN_ACCESS", "IN_PRIVACY_BY_DESIGN", "IN_EVIDENCE"],
    },
    {
        "id": "TH_PAYMENT",
        "label": "Digital payment, trust, fraud-detection, and Sybil-risk environment",
        "keywords": [
            "payment",
            "trust",
            "fraud detection",
            "sybil",
            "transaction pattern",
            "anomaly",
            "risk detection",
        ],
        "layer": "LY_TRANSACTION",
        "signal": "SG_PAYMENT",
        "interventions": ["IN_PAYMENT_CONTROLS", "IN_CHAIN_ANALYTICS", "IN_OFFRAMP"],
    },
    {
        "id": "TH_CYBER",
        "label": "Cyberattack, malware, platform-security, and infrastructure compromise",
        "keywords": [
            "cyberattack",
            "malware",
            "cybersecurity",
            "attack",
            "security",
            "vulnerability",
            "malicious",
            "threat",
        ],
        "layer": "LY_PLATFORM",
        "signal": "SG_CYBER",
        "interventions": ["IN_PLATFORM_SECURITY", "IN_ACCESS", "IN_EVIDENCE"],
    },
    {
        "id": "TH_GOVERNANCE",
        "label": "Platform governance, jurisdictional, and legal accountability gaps",
        "keywords": [
            "law",
            "regulation",
            "regulatory",
            "jurisdiction",
            "governance",
            "compliance",
            "legal",
            "accountability",
        ],
        "layer": "LY_GOVERNANCE",
        "signal": "SG_GOVERNANCE",
        "interventions": ["IN_GOVERNANCE_AUDIT", "IN_OFFRAMP", "IN_EVIDENCE"],
    },
]


LAYERS = [
    ("LY_PLATFORM", "Platform affordances: avatars, immersion, persistence, social presence"),
    ("LY_IDENTITY", "Identity-access layer: accounts, avatars, biometrics, credentials"),
    ("LY_ASSET", "Asset-market layer: NFTs, tokens, game items, virtual property"),
    ("LY_TRANSACTION", "Transaction-flow layer: wallets, payments, bridges, exchanges"),
    ("LY_GOVERNANCE", "Governance-control layer: DAOs, contracts, rules, jurisdiction"),
    ("LY_OPPORTUNITY", "Opportunity-formation layer: anonymity, deception, fragmented controls"),
    ("LY_DETECTION", "Detection-intervention layer: evidence, analytics, policy controls"),
]


SIGNALS = [
    ("SG_SCAM", "Scam campaign and social-engineering signals"),
    ("SG_AVATAR", "Avatar/account anomaly signals"),
    ("SG_NFT", "NFT wash-trade, provenance, and value-anomaly signals"),
    ("SG_WALLET", "Wallet clustering, mixer, bridge, and off-ramp exposure signals"),
    ("SG_CONTRACT", "Smart-contract, DAO, treasury, and permission-risk signals"),
    ("SG_PRIVACY", "Privacy, encryption, and traceability-loss signals"),
    ("SG_PAYMENT", "Payment, fraud-detection, trust, and Sybil signals"),
    ("SG_CYBER", "Cyberattack, malware, and platform compromise signals"),
    ("SG_GOVERNANCE", "Legal, compliance, and cross-jurisdiction signals"),
]


INTERVENTIONS = [
    ("IN_SCAM_MONITOR", "Scam-campaign monitoring and user harm response"),
    ("IN_ONBOARDING", "Risk-based onboarding and identity assurance"),
    ("IN_ACCESS", "Authentication, key custody, and access-control monitoring"),
    ("IN_PLATFORM_SECURITY", "Platform security monitoring and vulnerability response"),
    ("IN_PROVENANCE", "NFT/token provenance and asset-origin review"),
    ("IN_MARKETPLACE", "Marketplace behaviour monitoring and scam suppression"),
    ("IN_VALUATION", "Virtual-asset valuation and wash-trade anomaly review"),
    ("IN_CHAIN_ANALYTICS", "Wallet, bridge, mixer, and cross-chain analytics"),
    ("IN_PAYMENT_CONTROLS", "Digital-payment fraud controls and trust scoring"),
    ("IN_GOVERNANCE_AUDIT", "Smart-contract, DAO, and governance audit controls"),
    ("IN_OFFRAMP", "Exchange/off-ramp due diligence and reporting"),
    ("IN_EVIDENCE", "Investigation, evidence preservation, and case escalation"),
    ("IN_PRIVACY_BY_DESIGN", "Privacy-by-design controls with auditability"),
]


DIMENSIONS = [
    ("metaverse_platform_features", "Metaverse platform features"),
    ("crypto_ecosystem_features", "Cryptocurrency ecosystem features"),
    ("financial_crime_opportunities", "Financial crime opportunities"),
    ("modelling_analysis_intervention", "Modelling, analysis, and intervention"),
]


TYPE_COLOR = {
    "topic": "#315c72",
    "threat": "#9b3d42",
    "layer": "#6f5b2f",
    "signal": "#526d3f",
    "intervention": "#2f6f62",
    "document": "#6a5a9a",
    "dimension": "#4f6f98",
}


def clean_title(filename: str) -> str:
    text = re.sub(r"\.(pdf|txt)$", "", filename, flags=re.I)
    text = text.replace("_compressed", "").replace("_extract", "")
    text = text.replace("_", " ")
    return re.sub(r"\s+", " ", text).strip()


def short_label(text: str, max_len: int = 72) -> str:
    text = re.sub(r"\s+", " ", str(text)).strip()
    if len(text) <= max_len:
        return text
    cut = text[: max_len - 1].rsplit(" ", 1)[0]
    return cut + "..."


def wrap_text(text: str, width: int) -> list[str]:
    words = re.sub(r"\s+", " ", str(text)).strip().split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else current + " " + word
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def to_int(value: str) -> int:
    try:
        return int(float(value))
    except Exception:
        return 0


def node(
    node_id: str,
    label: str,
    node_type: str,
    detail: str = "",
    **attrs,
) -> dict:
    base = {
        "id": node_id,
        "label": label,
        "type": node_type,
        "detail": detail,
    }
    base.update(attrs)
    return base


def edge(
    source: str,
    target: str,
    relation: str,
    weight: float = 1.0,
    evidence: str = "",
    **attrs,
) -> dict:
    base = {
        "source": source,
        "target": target,
        "relation": relation,
        "weight": round(float(weight), 4),
        "evidence": evidence,
    }
    base.update(attrs)
    return base


def load_documents() -> list[dict]:
    with EVIDENCE_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    docs = []
    for row in rows:
        dim_counts = {key: to_int(row.get(key, "0")) for key, _ in DIMENSIONS}
        total_score = sum(dim_counts.values())
        text_blob = " ".join(
            [
                row.get("filename", ""),
                row.get("relevance", ""),
                row.get("top_evidence_1", ""),
                row.get("top_evidence_2", ""),
                row.get("top_evidence_3", ""),
            ]
        ).lower()
        threat_scores = {}
        for threat in THREATS:
            count = 0
            for keyword in threat["keywords"]:
                count += len(re.findall(re.escape(keyword.lower()), text_blob))
            if count:
                threat_scores[threat["id"]] = count

        if not threat_scores:
            # Keep every document in the graph even when keyword detection is sparse.
            best_dim = max(dim_counts, key=dim_counts.get)
            fallback = {
                "metaverse_platform_features": "TH_CYBER",
                "crypto_ecosystem_features": "TH_WALLET",
                "financial_crime_opportunities": "TH_SCAM",
                "modelling_analysis_intervention": "TH_PAYMENT",
            }[best_dim]
            threat_scores[fallback] = 1

        top_threats = sorted(threat_scores.items(), key=lambda x: (-x[1], x[0]))[:3]
        doc_no = row["doc_id"].split("_", 1)[0]
        title = clean_title(row.get("filename", row["doc_id"]))
        docs.append(
            {
                "id": "DOC_" + doc_no,
                "doc_no": doc_no,
                "source_doc_id": row["doc_id"],
                "title": title,
                "filename": row.get("filename", ""),
                "pages": to_int(row.get("pages", "0")),
                "words": to_int(row.get("extracted_words", "0")),
                "relevance": row.get("relevance", ""),
                "dim_counts": dim_counts,
                "total_score": total_score,
                "top_threats": top_threats,
                "evidence": [
                    row.get("top_evidence_1", ""),
                    row.get("top_evidence_2", ""),
                    row.get("top_evidence_3", ""),
                ],
            }
        )
    return docs


def build_graph(docs: list[dict]) -> tuple[list[dict], list[dict]]:
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    for topic in TOPICS:
        nodes[topic["id"]] = node(
            topic["id"],
            topic["id"] + ": " + topic["label"],
            "topic",
            f"{topic['prevalence']}% topic prevalence; dominant in {topic['documents']} PDFs.",
            prevalence=topic["prevalence"],
            documents=topic["documents"],
        )
        for threat_id in topic["threats"]:
            edges.append(
                edge(
                    topic["id"],
                    threat_id,
                    "topic-identifies-emerging-threat",
                    topic["prevalence"],
                )
            )

    for threat in THREATS:
        nodes[threat["id"]] = node(threat["id"], threat["label"], "threat")
        edges.append(edge(threat["id"], threat["layer"], "threat-operates-through-layer", 2))
        edges.append(edge(threat["id"], threat["signal"], "modelled-by-signal", 2))
        for intervention_id in threat["interventions"]:
            edges.append(edge(threat["id"], intervention_id, "intervention-point", 2))

    for layer_id, label in LAYERS:
        nodes[layer_id] = node(layer_id, label, "layer")
        edges.append(edge(layer_id, "LY_DETECTION", "feeds-detection-and-intervention", 1.2))

    for signal_id, label in SIGNALS:
        nodes[signal_id] = node(signal_id, label, "signal")
        edges.append(edge(signal_id, "LY_DETECTION", "analytical-signal", 1.2))

    for intervention_id, label in INTERVENTIONS:
        nodes[intervention_id] = node(intervention_id, label, "intervention")
        edges.append(edge("LY_DETECTION", intervention_id, "converted-into-control", 1))

    for dim_id, dim_label in DIMENSIONS:
        nodes["DIM_" + dim_id] = node(
            "DIM_" + dim_id,
            dim_label,
            "dimension",
            "Evidence dimension counted from the extracted PDF text.",
        )

    max_score = max((doc["total_score"] for doc in docs), default=1)
    max_dim = max((max(doc["dim_counts"].values()) for doc in docs), default=1)
    for doc in docs:
        doc_id = doc["id"]
        evidence_preview = " | ".join(short_label(x, 180) for x in doc["evidence"] if x)
        nodes[doc_id] = node(
            doc_id,
            f"{doc['doc_no']}: {short_label(doc['title'], 62)}",
            "document",
            evidence_preview,
            source_doc_id=doc["source_doc_id"],
            title=doc["title"],
            filename=doc["filename"],
            relevance=doc["relevance"],
            pages=doc["pages"],
            words=doc["words"],
            total_score=doc["total_score"],
            evidence=doc["evidence"],
        )
        for dim_id, dim_label in DIMENSIONS:
            count = doc["dim_counts"].get(dim_id, 0)
            if count > 0:
                edges.append(
                    edge(
                        doc_id,
                        "DIM_" + dim_id,
                        "document-supports-evidence-dimension",
                        1 + (count / max_dim) * 8,
                        f"{count} keyword/evidence hits for {dim_label}",
                        count=count,
                    )
                )
        for threat_id, count in doc["top_threats"]:
            edges.append(
                edge(
                    doc_id,
                    threat_id,
                    "document-indicates-threat",
                    1 + count,
                    f"{count} keyword matches in title/evidence excerpts",
                    count=count,
                )
            )
        if doc["total_score"] >= max_score * 0.55:
            # Make the strongest documents visible in the semantic layer as empirical anchors.
            strongest_threat = doc["top_threats"][0][0]
            edges.append(
                edge(
                    doc_id,
                    strongest_threat,
                    "high-evidence-anchor",
                    4,
                    f"High evidence score: {doc['total_score']}",
                )
            )

    return list(nodes.values()), edges


def write_csvs(nodes: list[dict], edges: list[dict]) -> None:
    node_keys = [
        "id",
        "label",
        "type",
        "detail",
        "prevalence",
        "documents",
        "source_doc_id",
        "filename",
        "relevance",
        "pages",
        "words",
        "total_score",
    ]
    with (PACK_DIR / "graph_nodes.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=node_keys, extrasaction="ignore")
        writer.writeheader()
        for n in nodes:
            writer.writerow(n)

    edge_keys = ["source", "target", "relation", "weight", "evidence", "count"]
    with (PACK_DIR / "graph_edges.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=edge_keys, extrasaction="ignore")
        writer.writeheader()
        for e in edges:
            writer.writerow(e)


def write_graphml(nodes: list[dict], edges: list[dict]) -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '<key id="label" for="node" attr.name="label" attr.type="string"/>',
        '<key id="type" for="node" attr.name="type" attr.type="string"/>',
        '<key id="detail" for="node" attr.name="detail" attr.type="string"/>',
        '<key id="relation" for="edge" attr.name="relation" attr.type="string"/>',
        '<key id="weight" for="edge" attr.name="weight" attr.type="double"/>',
        '<key id="evidence" for="edge" attr.name="evidence" attr.type="string"/>',
        '<graph id="MetaverseCryptoFinancialCrime" edgedefault="directed">',
    ]
    for n in nodes:
        lines.append(f'  <node id="{xml_escape(n["id"])}">')
        lines.append(f'    <data key="label">{xml_escape(str(n.get("label", "")))}</data>')
        lines.append(f'    <data key="type">{xml_escape(str(n.get("type", "")))}</data>')
        lines.append(f'    <data key="detail">{xml_escape(str(n.get("detail", "")))}</data>')
        lines.append("  </node>")
    for i, e in enumerate(edges, 1):
        lines.append(
            f'  <edge id="e{i}" source="{xml_escape(e["source"])}" target="{xml_escape(e["target"])}">'
        )
        lines.append(f'    <data key="relation">{xml_escape(str(e.get("relation", "")))}</data>')
        lines.append(f'    <data key="weight">{e.get("weight", 1)}</data>')
        lines.append(f'    <data key="evidence">{xml_escape(str(e.get("evidence", "")))}</data>')
        lines.append("  </edge>")
    lines.append("  </graph>")
    lines.append("</graphml>")
    (PACK_DIR / "graph_data.graphml").write_text("\n".join(lines), encoding="utf-8")


def svg_text(
    x: float,
    y: float,
    text: str,
    width: int,
    size: int = 12,
    anchor: str = "middle",
    fill: str = "#172026",
    weight: str = "500",
) -> str:
    lines = wrap_text(text, width)
    out = []
    start_y = y - (len(lines) - 1) * (size * 0.62)
    for i, line in enumerate(lines):
        out.append(
            f'<text x="{x:.1f}" y="{start_y + i * size * 1.2:.1f}" text-anchor="{anchor}" '
            f'font-size="{size}" font-weight="{weight}" fill="{fill}">{html.escape(line)}</text>'
        )
    return "\n".join(out)


def node_svg(
    n: dict,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str | None = None,
    node_type: str | None = None,
    extra_class: str = "",
) -> str:
    node_type = node_type or n.get("type", "")
    color = TYPE_COLOR.get(node_type, "#58606b")
    label = label if label is not None else n.get("label", n.get("id", ""))
    detail = n.get("detail", "")
    cls = f"node {node_type} {extra_class}".strip()
    return f"""
<g class="{cls}" data-type="{html.escape(node_type)}" data-node-id="{html.escape(n.get('id',''))}">
  <title>{html.escape(n.get('label',''))}&#10;{html.escape(detail)}</title>
  <rect x="{x - w/2:.1f}" y="{y - h/2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="7" fill="{color}" stroke="#172026" stroke-opacity="0.18" stroke-width="1.2"/>
  {svg_text(x, y - min(12, h * 0.13), label, max(12, int(w / 7.1)), 12 if w > 95 else 10, fill="#ffffff", weight="650")}
</g>
"""


def edge_svg(x1: float, y1: float, x2: float, y2: float, weight: float, relation: str = "") -> str:
    width = 0.6 + min(4.0, math.sqrt(max(weight, 0.1)) * 0.55)
    opacity = 0.18 + min(0.34, math.sqrt(max(weight, 0.1)) * 0.035)
    mid = (x1 + x2) / 2
    d = f"M {x1:.1f},{y1:.1f} C {mid:.1f},{y1:.1f} {mid:.1f},{y2:.1f} {x2:.1f},{y2:.1f}"
    return (
        f'<path class="edge" d="{d}" fill="none" stroke="#53616b" '
        f'stroke-width="{width:.2f}" stroke-opacity="{opacity:.2f}"><title>{html.escape(relation)}</title></path>'
    )


def semantic_layout(nodes: list[dict]) -> dict[str, tuple[float, float, float, float]]:
    by_type = defaultdict(list)
    for n in nodes:
        if n["type"] != "document" and n["type"] != "dimension":
            by_type[n["type"]].append(n)

    for t in by_type:
        by_type[t].sort(key=lambda n: n["id"])

    layout = {}

    def place(items, x, top, bottom, w, h):
        step = (bottom - top) / max(1, len(items) - 1)
        for i, n in enumerate(items):
            y = (top + bottom) / 2 if len(items) == 1 else top + i * step
            layout[n["id"]] = (x, y, w, h)

    topic_order = [next(n for n in nodes if n["id"] == t["id"]) for t in TOPICS]
    threat_order = [next(n for n in nodes if n["id"] == t["id"]) for t in THREATS]
    layer_order = [next(n for n in nodes if n["id"] == t[0]) for t in LAYERS]
    signal_order = [next(n for n in nodes if n["id"] == t[0]) for t in SIGNALS]
    intervention_order = [next(n for n in nodes if n["id"] == t[0]) for t in INTERVENTIONS]

    place(topic_order, 130, 100, 820, 190, 74)
    place(threat_order, 390, 80, 840, 210, 68)
    place(layer_order, 660, 95, 480, 210, 62)
    place(signal_order, 660, 570, 855, 210, 54)
    place(intervention_order, 930, 75, 855, 220, 54)
    return layout


def make_semantic_svg(nodes: list[dict], edges: list[dict]) -> str:
    layout = semantic_layout(nodes)
    edge_bits = []
    for e in edges:
        if e["source"] in layout and e["target"] in layout:
            x1, y1, w1, _ = layout[e["source"]]
            x2, y2, w2, _ = layout[e["target"]]
            edge_bits.append(edge_svg(x1 + w1 / 2, y1, x2 - w2 / 2, y2, e["weight"], e["relation"]))

    node_map = {n["id"]: n for n in nodes}
    node_bits = []
    for node_id, (x, y, w, h) in layout.items():
        n = node_map[node_id]
        label = n["label"]
        if n["type"] == "topic":
            label = label.replace(": ", "\n")
        node_bits.append(node_svg(n, x, y, w, h, label=label))

    legend = []
    legend_items = [
        ("topic", "Topic model output"),
        ("threat", "Emerging financial-crime environment"),
        ("layer", "Modelling layer"),
        ("signal", "Analytical signal"),
        ("intervention", "Intervention point"),
    ]
    for i, (typ, lab) in enumerate(legend_items):
        x = 105 + i * 210
        legend.append(
            f'<rect x="{x}" y="924" width="15" height="15" rx="3" fill="{TYPE_COLOR[typ]}"/>'
            f'<text x="{x+22}" y="936" font-size="12" fill="#26323a">{html.escape(lab)}</text>'
        )

    return f"""<svg class="graph-svg semantic-svg" xmlns="http://www.w3.org/2000/svg" width="1120" height="960" viewBox="0 0 1120 960" role="img" aria-label="Topic threat intervention network">
<style>
  .graph-title {{ font: 700 22px Arial, sans-serif; fill: #172026; }}
  .graph-subtitle {{ font: 400 13px Arial, sans-serif; fill: #4f5d66; }}
  text {{ font-family: Arial, sans-serif; }}
  .node {{ cursor: default; }}
  .edge {{ pointer-events: stroke; }}
</style>
<rect width="1120" height="960" fill="#f7f8f5"/>
<text x="54" y="42" class="graph-title">Full Topic-to-Threat-to-Intervention Graph</text>
<text x="54" y="66" class="graph-subtitle">Built locally from Round 5 topic modelling, Qwen evidence extraction, and the 59-document corpus.</text>
<text x="130" y="92" text-anchor="middle" font-size="12" font-weight="700" fill="#46545d">Topic model</text>
<text x="390" y="58" text-anchor="middle" font-size="12" font-weight="700" fill="#46545d">Emerging threat environment</text>
<text x="660" y="58" text-anchor="middle" font-size="12" font-weight="700" fill="#46545d">Model and analyse</text>
<text x="930" y="58" text-anchor="middle" font-size="12" font-weight="700" fill="#46545d">Intervention points</text>
{"".join(edge_bits)}
{"".join(node_bits)}
{"".join(legend)}
</svg>"""


def make_document_svg(nodes: list[dict], edges: list[dict], docs: list[dict]) -> str:
    node_map = {n["id"]: n for n in nodes}
    doc_nodes = [node_map[d["id"]] for d in docs]
    dim_nodes = [node_map["DIM_" + dim_id] for dim_id, _ in DIMENSIONS]
    threat_nodes = [node_map[t["id"]] for t in THREATS]

    layout: dict[str, tuple[float, float, float, float]] = {}
    cx, cy = 650.0, 620.0
    doc_radius = 480.0
    threat_radius = 275.0
    dim_radius = 135.0

    for i, n in enumerate(doc_nodes):
        angle = -math.pi / 2 + i * (2 * math.pi / len(doc_nodes))
        layout[n["id"]] = (cx + math.cos(angle) * doc_radius, cy + math.sin(angle) * doc_radius, 54, 30)

    for i, n in enumerate(threat_nodes):
        angle = -math.pi / 2 + i * (2 * math.pi / len(threat_nodes))
        layout[n["id"]] = (cx + math.cos(angle) * threat_radius, cy + math.sin(angle) * threat_radius, 122, 48)

    for i, n in enumerate(dim_nodes):
        angle = -math.pi / 2 + i * (2 * math.pi / len(dim_nodes))
        layout[n["id"]] = (cx + math.cos(angle) * dim_radius, cy + math.sin(angle) * dim_radius, 148, 52)

    edge_bits = []
    for e in edges:
        if e["source"] in layout and e["target"] in layout:
            # Keep the full graph, but cap visual line width to keep it readable.
            x1, y1, w1, _ = layout[e["source"]]
            x2, y2, w2, _ = layout[e["target"]]
            edge_bits.append(edge_svg(x1, y1, x2, y2, min(e["weight"], 7), e["relation"]))

    node_bits = []
    for n in dim_nodes + threat_nodes:
        x, y, w, h = layout[n["id"]]
        node_bits.append(node_svg(n, x, y, w, h, label=short_label(n["label"], 42)))

    for n in doc_nodes:
        x, y, w, h = layout[n["id"]]
        score = int(n.get("total_score", 0))
        color = "#6a5a9a" if "primary" in n.get("relevance", "") else "#8a7bb3"
        node_bits.append(
            f"""
<g class="node document" data-type="document" data-node-id="{html.escape(n['id'])}">
  <title>{html.escape(n.get('label',''))}&#10;Evidence score: {score}&#10;{html.escape(n.get('detail',''))}</title>
  <circle cx="{x:.1f}" cy="{y:.1f}" r="{11 + min(7, math.sqrt(max(score, 1)) / 5):.1f}" fill="{color}" stroke="#172026" stroke-opacity="0.18"/>
  <text x="{x:.1f}" y="{y+4:.1f}" text-anchor="middle" font-size="9" font-weight="700" fill="#ffffff">{html.escape(n['id'].replace('DOC_', ''))}</text>
</g>
"""
        )

    legend = """
<rect x="72" y="1095" width="16" height="16" rx="3" fill="#4f6f98"/><text x="96" y="1108" font-size="12" fill="#26323a">Evidence dimension</text>
<rect x="250" y="1095" width="16" height="16" rx="3" fill="#9b3d42"/><text x="274" y="1108" font-size="12" fill="#26323a">Threat environment</text>
<circle cx="458" cy="1103" r="9" fill="#6a5a9a"/><text x="475" y="1108" font-size="12" fill="#26323a">Document node, scaled by evidence score</text>
"""
    return f"""<svg class="graph-svg document-svg" xmlns="http://www.w3.org/2000/svg" width="1300" height="1140" viewBox="0 0 1300 1140" role="img" aria-label="Document evidence network">
<style>
  .graph-title {{ font: 700 22px Arial, sans-serif; fill: #172026; }}
  .graph-subtitle {{ font: 400 13px Arial, sans-serif; fill: #4f5d66; }}
  text {{ font-family: Arial, sans-serif; }}
  .node {{ cursor: default; }}
</style>
<rect width="1300" height="1140" fill="#f7f8f5"/>
<text x="56" y="42" class="graph-title">Full Document Evidence Network</text>
<text x="56" y="66" class="graph-subtitle">All 59 PDFs are included. Edges connect documents to evidence dimensions and detected threat environments.</text>
{"".join(edge_bits)}
{"".join(node_bits)}
{legend}
</svg>"""


def make_lifecycle_svg() -> str:
    stages = [
        ("1", "Platform affordance", "Avatars, immersive spaces, user accounts, social interaction, persistent commerce"),
        ("2", "Crypto rail", "Wallets, tokens, NFTs, smart contracts, bridges, exchanges, digital payments"),
        ("3", "Opportunity formation", "Pseudonymity, rapid value transfer, fragmented jurisdiction, social deception"),
        ("4", "Financial-crime pattern", "Laundering, scams, fraud, theft, wash trading, mule/off-ramp use"),
        ("5", "Analytical model", "Topic-model themes, document evidence, graph links, transaction and behaviour signals"),
        ("6", "Intervention point", "Onboarding, marketplace, access control, chain analytics, off-ramp due diligence, evidence preservation"),
    ]
    interventions = [
        (122, 300, "Design-time controls", "Privacy with auditability; security-by-design; asset rules"),
        (322, 300, "Entry controls", "Risk-based onboarding; wallet and account assurance"),
        (522, 300, "Market controls", "NFT provenance; wash-trade review; scam suppression"),
        (722, 300, "Flow controls", "Wallet clustering; bridge/mixer exposure; payment anomaly detection"),
        (922, 300, "Exit controls", "Exchange/off-ramp due diligence; suspicious activity escalation"),
        (1122, 300, "Case controls", "Evidence preservation; cross-platform investigation; reporting"),
    ]
    bits = [
        '<svg class="graph-svg lifecycle-svg" xmlns="http://www.w3.org/2000/svg" width="1240" height="520" viewBox="0 0 1240 520" role="img" aria-label="Intervention lifecycle map">',
        "<style>text{font-family:Arial,sans-serif}.edge{stroke:#53616b;stroke-width:2;stroke-opacity:.44;fill:none}.arrow{fill:#53616b}.title{font:700 22px Arial,sans-serif;fill:#172026}.subtitle{font:400 13px Arial,sans-serif;fill:#4f5d66}</style>",
        '<rect width="1240" height="520" fill="#f7f8f5"/>',
        '<text x="48" y="42" class="title">Lifecycle Map: Where to Model, Analyse, and Intervene</text>',
        '<text x="48" y="66" class="subtitle">The graph converts topic-modelled emerging threats into practical intervention points across the metaverse-crypto crime environment.</text>',
    ]
    y = 150
    for i, (num, title, desc) in enumerate(stages):
        x = 82 + i * 205
        color = ["#315c72", "#4f6f98", "#9b3d42", "#8b4b2d", "#526d3f", "#2f6f62"][i]
        bits.append(
            f'<g class="node lifecycle-stage" data-type="layer"><rect x="{x-70}" y="{y-55}" width="155" height="110" rx="7" fill="{color}" stroke="#172026" stroke-opacity=".16"/>'
        )
        bits.append(f'<circle cx="{x-48}" cy="{y-33}" r="15" fill="#ffffff" fill-opacity=".92"/><text x="{x-48}" y="{y-28}" text-anchor="middle" font-size="13" font-weight="700" fill="{color}">{num}</text>')
        bits.append(svg_text(x + 10, y - 12, title, 17, 13, fill="#ffffff", weight="700"))
        bits.append(svg_text(x + 8, y + 30, desc, 22, 10, fill="#ffffff", weight="500"))
        bits.append("</g>")
        if i < len(stages) - 1:
            x2 = x + 125
            bits.append(f'<path class="edge" d="M{x+86},{y} L{x2},{y}"/><path class="arrow" d="M{x2},{y} l-8,-5 v10 z"/>')
    bits.append('<text x="48" y="262" font-size="13" font-weight="700" fill="#46545d">Intervention control surface</text>')
    for x, y2, title, desc in interventions:
        bits.append(
            f'<g class="node intervention" data-type="intervention"><rect x="{x-82}" y="{y2}" width="164" height="118" rx="7" fill="#2f6f62" stroke="#172026" stroke-opacity=".16"/>'
        )
        bits.append(svg_text(x, y2 + 34, title, 20, 13, fill="#ffffff", weight="700"))
        bits.append(svg_text(x, y2 + 76, desc, 25, 10, fill="#ffffff", weight="500"))
        bits.append("</g>")
        bits.append(f'<path d="M{x},{y2} C{x},{260} {x},{245} {x},{210}" fill="none" stroke="#2f6f62" stroke-width="1.4" stroke-opacity=".42" stroke-dasharray="5 5"/>')
    bits.append("</svg>")
    return "\n".join(bits)


def write_intervention_matrix(nodes: list[dict], edges: list[dict]) -> None:
    threat_lookup = {t["id"]: t["label"] for t in THREATS}
    int_lookup = dict(INTERVENTIONS)
    signal_lookup = dict(SIGNALS)
    layer_lookup = dict(LAYERS)
    threat_doc_counts = Counter()
    for e in edges:
        if e["relation"] in {"document-indicates-threat", "high-evidence-anchor"} and e["target"].startswith("TH_"):
            threat_doc_counts[e["target"]] += 1

    rows = []
    for t in THREATS:
        rows.append(
            {
                "threat_environment": threat_lookup[t["id"]],
                "modelling_layer": layer_lookup[t["layer"]],
                "analytical_signal": signal_lookup[t["signal"]],
                "intervention_points": "; ".join(int_lookup[i] for i in t["interventions"]),
                "linked_document_count": threat_doc_counts[t["id"]],
                "topic_links": "; ".join(topic["id"] for topic in TOPICS if t["id"] in topic["threats"]),
            }
        )
    with (PACK_DIR / "intervention_matrix.csv").open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "threat_environment",
            "modelling_layer",
            "analytical_signal",
            "intervention_points",
            "linked_document_count",
            "topic_links",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def make_html(nodes: list[dict], edges: list[dict], docs: list[dict], semantic_svg: str, document_svg: str, lifecycle_svg: str) -> str:
    type_counts = Counter(n["type"] for n in nodes)
    relation_counts = Counter(e["relation"] for e in edges)
    docs_sorted = sorted(docs, key=lambda d: (-d["total_score"], d["doc_no"]))
    top_doc_rows = []
    for d in docs_sorted:
        threats = ", ".join(t for t, _ in d["top_threats"])
        dims = ", ".join(f"{key.replace('_', ' ')}={value}" for key, value in d["dim_counts"].items())
        top_doc_rows.append(
            f"<tr data-search='{html.escape((d['doc_no'] + ' ' + d['title'] + ' ' + d['relevance']).lower())}'>"
            f"<td>{html.escape(d['doc_no'])}</td><td>{html.escape(short_label(d['title'], 95))}</td>"
            f"<td>{d['total_score']}</td><td>{html.escape(d['relevance'])}</td>"
            f"<td>{html.escape(threats)}</td><td>{html.escape(dims)}</td></tr>"
        )

    graph_data = {
        "created_by": "Codex local/free graph builder",
        "cost_boundary": "No paid API, no cloud graph service, no external web libraries.",
        "corpus": {"documents": len(docs), "source": str(EVIDENCE_CSV)},
        "nodes": nodes,
        "edges": edges,
    }
    graph_json = json.dumps(graph_data, ensure_ascii=False)
    safe_graph_json = graph_json.replace("<", "\\u003c").replace("</script", "<\\/script")
    stats_cards = [
        ("Documents", len(docs)),
        ("Graph nodes", len(nodes)),
        ("Graph edges", len(edges)),
        ("Topic model themes", len(TOPICS)),
        ("Threat environments", len(THREATS)),
        ("Intervention points", len(INTERVENTIONS)),
    ]
    stats_html = "".join(
        f"<div class='stat'><strong>{value}</strong><span>{html.escape(label)}</span></div>"
        for label, value in stats_cards
    )
    type_html = "".join(
        f"<label><input type='checkbox' data-type-toggle='{html.escape(typ)}' checked> {html.escape(typ)} ({count})</label>"
        for typ, count in sorted(type_counts.items())
    )
    relation_html = "".join(
        f"<li><strong>{html.escape(rel)}</strong>: {count}</li>" for rel, count in sorted(relation_counts.items())
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Free Full Graph Pack - Metaverse Crypto Financial Crime</title>
<style>
  :root {{
    --ink: #172026;
    --muted: #58656f;
    --line: #d8ddd8;
    --paper: #f7f8f5;
    --panel: #ffffff;
    --accent: #315c72;
    --teal: #2f6f62;
    --red: #9b3d42;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: Arial, Helvetica, sans-serif;
    color: var(--ink);
    background: var(--paper);
  }}
  header {{
    padding: 28px 34px 18px;
    border-bottom: 1px solid var(--line);
    background: #ffffff;
  }}
  h1 {{
    margin: 0 0 8px;
    font-size: 26px;
    line-height: 1.15;
    letter-spacing: 0;
  }}
  .sub {{
    margin: 0;
    max-width: 1050px;
    color: var(--muted);
    line-height: 1.45;
    font-size: 14px;
  }}
  .stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
    gap: 10px;
    padding: 16px 34px 6px;
  }}
  .stat {{
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 12px 13px;
  }}
  .stat strong {{
    display: block;
    font-size: 22px;
    margin-bottom: 3px;
  }}
  .stat span {{
    color: var(--muted);
    font-size: 12px;
  }}
  nav {{
    display: flex;
    gap: 8px;
    padding: 16px 34px 10px;
    flex-wrap: wrap;
  }}
  button {{
    border: 1px solid var(--line);
    background: #ffffff;
    color: var(--ink);
    border-radius: 7px;
    padding: 9px 12px;
    font-weight: 700;
    cursor: pointer;
  }}
  button.active {{
    background: var(--accent);
    border-color: var(--accent);
    color: #ffffff;
  }}
  main {{ padding: 0 34px 34px; }}
  section.view {{ display: none; }}
  section.view.active {{ display: block; }}
  .toolbar {{
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin: 10px 0 12px;
    color: var(--muted);
    font-size: 13px;
  }}
  .toolbar label {{
    display: inline-flex;
    gap: 6px;
    align-items: center;
    white-space: nowrap;
  }}
  .graph-frame {{
    overflow: auto;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: #ffffff;
  }}
  .graph-frame svg {{
    display: block;
    max-width: none;
  }}
  .graph-frame .node.dimmed,
  .graph-frame .edge.dimmed {{
    opacity: .08;
  }}
  .two-col {{
    display: grid;
    grid-template-columns: minmax(250px, 340px) 1fr;
    gap: 14px;
    align-items: start;
  }}
  .panel {{
    background: #ffffff;
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 14px;
  }}
  h2 {{
    font-size: 17px;
    margin: 0 0 9px;
  }}
  ul {{
    margin: 0;
    padding-left: 18px;
    color: var(--muted);
    line-height: 1.45;
    font-size: 13px;
  }}
  input[type="search"] {{
    width: min(520px, 100%);
    border: 1px solid var(--line);
    border-radius: 7px;
    padding: 10px 11px;
    font-size: 14px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    background: #ffffff;
    border: 1px solid var(--line);
    border-radius: 8px;
    overflow: hidden;
    font-size: 12px;
  }}
  th, td {{
    padding: 8px 9px;
    border-bottom: 1px solid var(--line);
    text-align: left;
    vertical-align: top;
  }}
  th {{
    background: #edf1ef;
    font-size: 11px;
    color: #354149;
  }}
  .downloads {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
    gap: 10px;
  }}
  .downloads a {{
    display: block;
    padding: 12px 13px;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: #ffffff;
    color: var(--accent);
    font-weight: 700;
    text-decoration: none;
  }}
  @media (max-width: 820px) {{
    header, .stats, nav, main {{ padding-left: 16px; padding-right: 16px; }}
    .two-col {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
<header>
  <h1>Free Full Graph Pack: Metaverse-Crypto Financial Crime Environments</h1>
  <p class="sub">This is a standalone local file. It uses the Round 5 topic-model themes, the local Qwen evidence extraction, and the 59-document corpus evidence table to model, analyse, and identify intervention points. No paid service, no Zep Cloud, no external JavaScript library.</p>
</header>
<div class="stats">{stats_html}</div>
<nav>
  <button class="active" data-view="semantic">Topic to Intervention Graph</button>
  <button data-view="document">Full Document Evidence Graph</button>
  <button data-view="lifecycle">Lifecycle Intervention Map</button>
  <button data-view="table">Evidence Table</button>
  <button data-view="files">Export Files</button>
</nav>
<main>
  <section class="view active" id="semantic">
    <div class="toolbar">{type_html}</div>
    <div class="graph-frame">{semantic_svg}</div>
  </section>
  <section class="view" id="document">
    <div class="toolbar">Every corpus document is included; document circles are scaled by evidence score.</div>
    <div class="graph-frame">{document_svg}</div>
  </section>
  <section class="view" id="lifecycle">
    <div class="graph-frame">{lifecycle_svg}</div>
  </section>
  <section class="view" id="table">
    <div class="toolbar"><input id="docSearch" type="search" placeholder="Search documents, relevance labels, or document IDs"></div>
    <table>
      <thead><tr><th>Doc</th><th>Title</th><th>Score</th><th>Relevance</th><th>Threat links</th><th>Evidence dimensions</th></tr></thead>
      <tbody id="docRows">{''.join(top_doc_rows)}</tbody>
    </table>
  </section>
  <section class="view" id="files">
    <div class="two-col">
      <div class="panel">
        <h2>Graph Relations</h2>
        <ul>{relation_html}</ul>
      </div>
      <div class="panel">
        <h2>Included Exports</h2>
        <div class="downloads">
          <a href="topic_threat_intervention_full.svg">Static topic-to-intervention SVG</a>
          <a href="document_evidence_network_full.svg">Static document evidence SVG</a>
          <a href="intervention_lifecycle_map.svg">Lifecycle SVG</a>
          <a href="graph_data.json">Graph JSON</a>
          <a href="graph_nodes.csv">Nodes CSV</a>
          <a href="graph_edges.csv">Edges CSV</a>
          <a href="graph_data.graphml">GraphML for Gephi/yEd</a>
          <a href="intervention_matrix.csv">Intervention matrix CSV</a>
        </div>
      </div>
    </div>
  </section>
</main>
<script id="graphData" type="application/json">{safe_graph_json}</script>
<script>
  const buttons = [...document.querySelectorAll('nav button')];
  const views = [...document.querySelectorAll('.view')];
  buttons.forEach(button => {{
    button.addEventListener('click', () => {{
      buttons.forEach(b => b.classList.toggle('active', b === button));
      views.forEach(v => v.classList.toggle('active', v.id === button.dataset.view));
    }});
  }});
  document.querySelectorAll('[data-type-toggle]').forEach(input => {{
    input.addEventListener('change', () => {{
      const type = input.dataset.typeToggle;
      document.querySelectorAll('.graph-frame .node[data-type="' + type + '"]').forEach(n => n.classList.toggle('dimmed', !input.checked));
    }});
  }});
  const search = document.getElementById('docSearch');
  if (search) {{
    search.addEventListener('input', () => {{
      const q = search.value.trim().toLowerCase();
      document.querySelectorAll('#docRows tr').forEach(row => {{
        row.style.display = !q || row.dataset.search.includes(q) ? '' : 'none';
      }});
    }});
  }}
</script>
</body>
</html>"""


def write_readme(docs: list[dict], nodes: list[dict], edges: list[dict]) -> None:
    doc_counts = Counter()
    for d in docs:
        for tid, _ in d["top_threats"]:
            doc_counts[tid] += 1
    threat_lines = []
    threat_lookup = {t["id"]: t["label"] for t in THREATS}
    for tid, count in doc_counts.most_common():
        threat_lines.append(f"- {threat_lookup.get(tid, tid)}: {count} linked documents")

    readme = f"""# Free Full Graph Pack

This graph pack was generated entirely locally from the existing Round 5 outputs:

- Source evidence table: `{EVIDENCE_CSV}`
- Document count: {len(docs)}
- Nodes: {len(nodes)}
- Edges: {len(edges)}
- Cost boundary: no paid API, no Zep Cloud, and no external web libraries.

## Main files

- `full_interactive_graph_pack.html` - standalone browser graph pack with three graph views.
- `topic_threat_intervention_full.svg` - static topic-model to intervention graph.
- `document_evidence_network_full.svg` - static network containing all 59 documents.
- `intervention_lifecycle_map.svg` - lifecycle map of modelling, analysis, and intervention points.
- `graph_data.json` - complete node/edge graph data.
- `graph_nodes.csv` and `graph_edges.csv` - tabular export for audit or reuse.
- `graph_data.graphml` - importable into free graph tools such as Gephi or yEd.
- `intervention_matrix.csv` - threat-to-signal-to-intervention matrix.

## Most connected threat environments

{chr(10).join(threat_lines)}

## Interpretation note

The graph is an analytical model, not a claim that every document proves every threat. Document-to-threat edges are generated from the extracted title and evidence snippets using transparent local keyword rules, while the topic-to-threat structure follows the verified Round 5 topic-model labels and prevalence values.
"""
    (PACK_DIR / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    docs = load_documents()
    nodes, edges = build_graph(docs)

    graph_data = {
        "created_by": "Codex local/free graph builder",
        "cost_boundary": "No paid API, no Zep Cloud, no external web libraries.",
        "source_evidence_table": str(EVIDENCE_CSV),
        "summary": {
            "documents": len(docs),
            "nodes": len(nodes),
            "edges": len(edges),
            "topics": len(TOPICS),
            "threat_environments": len(THREATS),
            "interventions": len(INTERVENTIONS),
        },
        "topics": TOPICS,
        "threats": THREATS,
        "layers": LAYERS,
        "signals": SIGNALS,
        "interventions": INTERVENTIONS,
        "nodes": nodes,
        "edges": edges,
    }
    (PACK_DIR / "graph_data.json").write_text(json.dumps(graph_data, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csvs(nodes, edges)
    write_graphml(nodes, edges)
    write_intervention_matrix(nodes, edges)

    semantic_svg = make_semantic_svg(nodes, edges)
    document_svg = make_document_svg(nodes, edges, docs)
    lifecycle_svg = make_lifecycle_svg()
    (PACK_DIR / "topic_threat_intervention_full.svg").write_text(semantic_svg, encoding="utf-8")
    (PACK_DIR / "document_evidence_network_full.svg").write_text(document_svg, encoding="utf-8")
    (PACK_DIR / "intervention_lifecycle_map.svg").write_text(lifecycle_svg, encoding="utf-8")
    (PACK_DIR / "full_interactive_graph_pack.html").write_text(
        make_html(nodes, edges, docs, semantic_svg, document_svg, lifecycle_svg),
        encoding="utf-8",
    )
    write_readme(docs, nodes, edges)

    print(json.dumps(graph_data["summary"], indent=2))
    print(str(PACK_DIR))


if __name__ == "__main__":
    main()

```
