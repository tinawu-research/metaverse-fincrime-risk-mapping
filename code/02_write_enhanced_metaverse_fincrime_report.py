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
