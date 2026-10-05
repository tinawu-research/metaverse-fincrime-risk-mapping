> **Delivery copy (2026-10-05).** Sanitised from the 2026-09-29 draft: scheduler/account/host identifiers, personal machine details and author names (replaced by reviewer codes) removed; no other change. References to project-relative paths (`qwen_65docs/...`, `internal_reviewer_snapshot_20260929/...`) name files of the project working directory, not files of this delivery; the delivered counterparts are listed in the attachment manifest.

# Deterministic Rules and Code — Evidence Extraction for the Qwen Pipeline

**Status: draft for author review.** This documents the fixed, non-model
rules that turned each document's already-extracted text into what Qwen
actually saw (keyword categories, relevance tiering, excerpt selection,
`evidence_score`), and the separate input-construction step that produced
the concatenated text those rules run over. It does not cover PDF→text
extraction itself (see §7, scope boundary with `Electronic_Supplement_A1`).

**Revised 2026-09-29 (targeted correction pass, four items):** (1) §2's
lexicon table previously showed a human-readable, singular/plural-collapsed
summary labelled "verbatim" — it was not; this section now gives the
literal source list first, with programmatically counted totals, and the
readable summary separately and explicitly marked as non-verbatim. (2) §6's
"not the same quantity" wording about `evidence_score` is corrected — it
*is* the same underlying sum, used two different ways. (3) §7 previously
described `document_evidence_65.json` as if it were raw text the rules
operate on; it is actually the rules' *output*. §7 is rewritten with the
full, verified input chain and code location for
`build_input_from_extracted.py` (now also copied into `code_copies/`). (4)
This file's own opening cross-reference pointed to the wrong section (§5
instead of §7) for the extraction-scope boundary — fixed.

## 1. Code locations and provenance

| Role | File (source location) | sha256 | Modified for this round? |
|---|---|---|---|
| Rule logic itself: lexicon, counting, sentence scoring, relevance tiering, excerpt selection | `metaverse-fincrime-reproducibility-package/code/01_local_qwen_metaverse_fincrime_analysis.py` | `c6f5c4edfae08ab063b75bb75cab936cf211b745b6fae6879efa67049c201764` | **No.** Same file used for the historical 59-document run; imported unchanged (by path, via `importlib`) for the 65-document run — not copied and edited. |
| Input-construction step (concatenates per-document extracted JSON into the one text file the rule logic parses — see §7) | `qwen_65docs/preflight/scripts/build_input_from_extracted.py` | `a0b6a85f471be6b195bb7ade30069ed803a83e414d3b2e8d7ea2d244b262e437` | New script for the 65-doc preflight round; calls no rule/counting logic itself (reformats only — see §7) |
| Stage ① wrapper (calls the rule logic above on the 65-document input, adds `evidence_score`) | `qwen_65docs/preflight/scripts/run_rules_stage1.py` | `34298078442c2a84b76a4225716fef0eeed24ee5cd3c978b8a54d9c29d2b6e61` | New wrapper written for the 65-doc preflight round; the rule functions it calls are unmodified imports (row 1) |
| Stage ② driver (calls `build_batch_prompt`/`build_final_prompt`/`make_doc_digest` unchanged, talks to Ollama) | `qwen_65docs/qwen/scripts/run_stage2_qwen.py` | `a3f11320e1a5b3d01ef964599902fe7a4b05ab13889393c4648115bb1fd8fc66` | New driver written for this run; the prompt-building functions it imports are unmodified (row 1) |

**Revised 2026-09-29: all four files, including `build_input_from_extracted.py`
(added this round), are verbatim copies in `code_copies/`**, with sha256
matching the table above (independently recomputed against each file's
source path this round, not carried forward unchecked from an earlier
pass).

**Confirmed and unmodified vs. not independently re-derived:** the sha256 in
row 1 was independently recomputed this round directly against the file at
its source path; the rule *logic* itself (the `LEXICONS` dict and every
function below) was read directly from that file, not from a summary or a
prior description — nothing below is reconstructed from memory or inferred
from output text. §2's counts below were computed **programmatically**
(`len()` on the actual parsed list), not counted by eye, specifically to
avoid repeating the transcription error this round corrects.

## 2. Keyword lexicon: the literal source list, then a programmatic count

**The literal `LEXICONS` dict, lines 24–53 of
`01_local_qwen_metaverse_fincrime_analysis.py`, reproduced character-for-
character (this is the verbatim source — not the readable summary further
below, which is explicitly a separate, secondary thing):**

```python
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
```

**Programmatically computed entry counts** (this round: the module was
loaded via `importlib` from its source path and `len(LEXICONS[category])`
was read directly — not counted from the printed text above by eye):

| Category | Entry count | Corrected from (prior draft's miscount) |
|---|---:|---:|
| `metaverse_platform_features` | **33** | 29 |
| `crypto_ecosystem_features` | **34** | 28 |
| `financial_crime_opportunities` | **24** | 22 |
| `modelling_analysis_intervention` | **33** | 30 |
| **Total** | **124** | 109 |

**Why the prior draft's counts were wrong, stated plainly:** the previous
version of this section collapsed singular/plural or slash-joined pairs
(e.g. writing `"virtual world(s)"` for the list's two separate entries
`"virtual world"` and `"virtual worlds"`; `"cryptocurrency/cryptocurrencies"`
for two separate entries) into single displayed items, which undercounted
every category, while the category-total label itself
(`modelling_analysis_intervention`: "30 terms") was carried over from an
even earlier miscount and did not even match its own displayed,
comma-separated list (which had 33 distinct displayed items — the label was
wrong on its own terms, independent of the collapsing issue). **There is no
`(s)`-suffix or slash-alternation feature anywhere in the actual code** —
`"virtual world"` and `"virtual worlds"` are two independent strings in the
Python list, each separately turned into its own `\bterm\b` regex by
`count_terms()` (§3). Presenting them as one collapsed entry misrepresented
the source, even though it did not change what the code actually matches.

**Separate, non-verbatim, human-readable summary** (for quick scanning
only — do **not** use this for a term count; use the table above):
`metaverse_platform_features` covers metaverse/virtual-world/avatar/VR-AR-XR
terms, virtual assets and NFTs, and identity/privacy/social terms;
`crypto_ecosystem_features` covers cryptocurrency, blockchain, wallets,
exchanges, DeFi/smart-contract/DAO terms, and mixers/privacy coins;
`financial_crime_opportunities` covers laundering, fraud/scam/phishing,
terrorist financing, sanctions, and named offence categories;
`modelling_analysis_intervention` covers KYC/CDD, regulation/compliance,
detection/monitoring/forensic/analytics terms, and named intervention or
governance mechanisms. This paragraph is a comprehension aid only; it
deliberately does not attempt to list or count individual terms.

## 3. Counting rule

`count_terms()` (lines 84–93): for each of the 124 literal lexicon entries
in §2's source list above, count case-insensitive, **word-boundary-anchored**
regex matches (`\bterm\b`) in the document's lowercased text. A document's
`category_totals[category]` is the sum of all its category's terms' match
counts. This is a simple literal/phrase count over the exact strings in the
list — not stemmed, not fuzzy-matched, and **not merged by singular/plural
or any other relationship**: `"laundering"` and `"money laundering"` are
two separate list entries and are counted separately if both literal
strings are present and both match; `"virtual world"` and `"virtual
worlds"` are likewise two separate entries, each matched independently.
Nothing in `count_terms()` treats a plural or a hyphen variant as
equivalent to its singular/base form unless both forms are separately
present in the list.

## 4. Sentence/excerpt selection rule

1. **Splitting** (`sentence_split()`, lines 96–98): the document text is
   split on sentence-ending punctuation followed by whitespace, or on
   blank-line breaks (`(?<=[.!?])\s+|\n{2,}`); each resulting chunk is
   whitespace-normalised and **kept only if ≥70 characters**. This is why
   some excerpts are not full sentences — a table row or caption fragment
   that happens to exceed 70 characters after whitespace normalisation
   passes this filter unchanged.
2. **Scoring** (`score_sentence()`, lines 101–118): for each candidate
   chunk, term-count per category is computed (§3's rule, applied at
   sentence level); `score = Σ(category_count × weight)` where
   `financial_crime_opportunities` has weight **3** and the other three
   categories have weight **2**, **plus 2 points per distinct category with
   at least one hit**, **plus a flat +3 bonus** if the sentence has both
   `metaverse_platform_features` and `crypto_ecosystem_features` hits, **plus
   another flat +3 bonus** if it has both `financial_crime_opportunities`
   and `modelling_analysis_intervention` hits.
3. **Selection** (`analyse_document()`, lines 131–148): all scored chunks
   (score > 0) are ranked descending by score. Chunks are then taken in rank
   order, truncated to 700 characters, and deduplicated by the lowercase
   first-120-character prefix (so two excerpts starting nearly identically
   are treated as one); the loop stops once **7** excerpts are collected per
   document. Only the **top 5** of those 7 are ever placed into a batch
   prompt (`item["snippets"][:5]` in `make_doc_digest()`) — the 6th/7th are
   computed and stored in `document_evidence_65.json` but never sent to
   Qwen.

## 5. Relevance-tier threshold (`analyse_document()`, lines 150–158)

Applied in this fixed order:

1. If `category_totals["financial_crime_opportunities"] ≥ 15` **and**
   `category_totals["crypto_ecosystem_features"] ≥ 15` → **"primary
   financial-crime/crypto evidence."**
2. Else if the sum of all four category totals ≥ 80 → **"highly relevant
   platform/security evidence."**
3. Else if that sum ≥ 25 → **"supporting contextual evidence."**
4. Else → **"peripheral or background evidence."**

For the 65-document corpus, only tiers 1 and 2 are actually populated: 17
documents in tier 1, 48 in tier 2, 0 in tiers 3–4 (17 + 48 = 65). See
`qwen_65docs/review/handoff_20260928/03_keyword_counts_and_classification.md`
for the cross-checked totals and the composition breakdown (14 of the 17
tier-1 documents carried over from the 59-document corpus; 3 of the 7 newly
added documents are also tier 1).

## 6. `evidence_score`: the same sum as §5's threshold, used for a different purpose — not an evidence-quality score

**Corrected 2026-09-29: an earlier version of this section said
`evidence_score` was "not the same quantity" as the relevance-tier sum in
§5 rule 2. That was imprecise. Restated precisely below.**

`evidence_score = Σ(category_totals.values())` — computed in
`run_rules_stage1.py` (Stage ① wrapper, not in the imported rule-logic file
itself). **This is arithmetically the identical four-category sum that §5
rule 2 compares against its 80/25 thresholds** — for any given document,
`evidence_score` and "the sum used in the relevance-tier rule" are the same
number, not two different computations that happen to agree.

**What differs is how that one number is used, not what it is:**

- In §5, the sum is compared against fixed thresholds (`≥ 80`, `≥ 25`) to
  assign one of four **categorical relevance-tier labels** to a document —
  a classification use.
- As `evidence_score`, the same sum is instead used only to **rank** the 65
  documents against each other, so the top 20 by this ranking can be passed
  (as metadata only, no excerpt text) to the final-synthesis call — a
  continuous, comparative-ranking use, with no threshold of its own.

`run_stage2_qwen.py` cross-checks this identity at load time (lines
282–283: raises `SystemExit` if `evidence_score != sum(category_totals.values())`
for any document), confirming the pipeline itself relies on these being the
same number — it is not treating them as independent quantities either.

**`evidence_score` is not a measure of evidence quality, reliability, or
substantiveness.** It is a raw count of keyword-boundary matches across
four fixed lexicons (§2–§3) — a document can score highly by containing
many keyword hits in table-of-contents-style enumerations, repeated
boilerplate, or a long reference list using those terms, without any of
those hits reflecting a substantively strong or well-evidenced discussion.
Nothing in this pipeline evaluates the *quality* of a document's discussion
of any topic; `evidence_score` and the relevance tiers are both built from
the unnormalised sum of keyword-match counts across the four categories —
not normalised by document length, page count, or word count — used
respectively for ranking and for a coarse categorical split, not for
assessing evidentiary strength.

## 7. Input chain: from the extracted per-document JSON to `document_evidence_65.json`

**Corrected 2026-09-29: an earlier version of this section described
`document_evidence_65.json` as the already-extracted text the counting
rules "operate on." That is backwards — `document_evidence_65.json` is the
rules' *output*, not their input.** The actual chain, verified this round
against the two scripts' own code (not restated from memory):

**Step 1 — per-document extracted JSON (upstream input, not produced by
this Qwen pipeline's own code).** Each of the 65 documents has a JSON file
at `CHBR_LDA_comparison_20260915/complete_lda/Complete_LDA_Results/private/extracted/<doc_id>.json`,
with (at minimum) a `raw_pages` field: a list of strings, one per PDF page,
as extracted by the upstream PDF→text step. **This JSON file's own
production (the PDF→text extraction itself) is owned by
`Electronic_Supplement_A1`, not by this Qwen supplement** (§7's original
scope statement, unchanged in substance, only relocated — see the
cross-reference fix at the top of this file). A companion manifest,
`incoming/Electronic_Supplement_A1/tables/corpus_manifest.csv`, carries one
row per document with columns including `document_id`, `filename`,
`page_count`, `raw_words`, `cleaned_words`, `sha256`, `status`, plus
LDA-specific columns not used at this step (`normalized_tokens`,
`reference_removed`, `long_word_fraction`).

**Step 2 — `build_input_from_extracted.py` (verbatim copy now in
`code_copies/`, sha256 in §1) concatenates, without cleaning the text
itself.** For each document, in the manifest's row order, this script:

1. Reads that document's `raw_pages` list from its extracted JSON.
2. **Validates** (fails loudly, writes nothing, if any check fails):
   `len(raw_pages)` equals the manifest's `page_count`; the whitespace-split
   word count of the joined pages equals the manifest's `raw_words` field
   exactly; no page line accidentally starts with the literal text
   `"DOC_ID:"` (a parser-hazard guard); every manifest `document_id` has a
   corresponding JSON file and vice versa, with no duplicate IDs.
3. **Joins** the page strings with a blank line (`"\n\n"`) and `.strip()`s
   the result — the **only** transformation applied to the page text
   itself at this step (removing leading/trailing whitespace from the
   joined whole; no lowercasing, no stopword removal, no lemmatization, no
   deduplication of repeated content, no reference-list stripping).
4. **Wraps** the joined, stripped text in a fixed header block (`DOC_ID:`,
   `FILENAME:`, `PAGES:`, `EXTRACTED_WORDS:`, separated by `"="×100` lines)
   — this is the exact block format `parse_documents()` (in the imported
   rule-logic file) expects to split back apart in Step 3.
5. **Writes** the concatenation of all 65 such blocks to one file,
   `qwen_65docs/preflight/all_extracted_text_65docs.txt` (this is the file
   §4's excerpt-selection rule and §3's counting rule actually run over),
   plus a separate audit manifest (`build_input_manifest.csv`) recording,
   per document, the word-count field actually used
   (`word_count_field_used: raw_words`) and, for cross-reference only, the
   manifest's `cleaned_words` value under the column
   `cleaned_words_manifest` — **`cleaned_words` is recorded but never read
   back into the pipeline; it does not affect the text written to
   `all_extracted_text_65docs.txt` or anything computed from it.**

**Concrete example of the raw-vs-cleaned distinction, read directly from
`build_input_manifest.csv`:** document `D569a973fcbb6` has
`extracted_words` (= `raw_words`, the field actually used) of **9,745**,
against a recorded `cleaned_words_manifest` value of **8,650** — a
different, smaller number from the LDA side that this pipeline's own text
and counts never incorporate.

**What "cleaning" actually happens at this step, precisely:** whitespace
normalisation from joining pages and one `.strip()` call — nothing else.
**What is explicitly LDA-specific and not used here:** `cleaned_words`,
`normalized_tokens`, and `reference_removed` (a per-document flag for
whether bibliographic references were stripped during the LDA pipeline's
own preprocessing) are all present as columns in the shared
`corpus_manifest.csv` but are **not read** by `build_input_from_extracted.py`
(only `document_id`, `filename`, `page_count`, `raw_words`, `cleaned_words`
— the last read only to be copied into the audit manifest, not used
computationally — `sha256`, and `status` are read; confirmed directly from
the script's own `needed` column-check set). Any lemmatization, stopword
removal, or reference-removal the LDA pipeline performs for its own topic
modelling is therefore **not** applied to the text Qwen's rule-based
pipeline counts terms in or excerpts snippets from.

**Step 3 — `run_rules_stage1.py` (verbatim copy in `code_copies/`) runs the
counting/scoring/tiering rules and produces the output.** This script:
loads `all_extracted_text_65docs.txt` (Step 2's output), calls the
unmodified `parse_documents()` (splits the concatenated text back into 65
per-document dicts using the header block from Step 2.4) and
`analyse_document()` (§§2–5 of this file: keyword counting, excerpt
selection, relevance tiering — all as already documented above) from the
imported, unmodified rule-logic file, adds `evidence_score` (§6), and
writes the results — **this is where `document_evidence_65.json` (plus
`document_evidence_table_65.csv` and `manifest_65.json`) is produced, as
output, not consumed as input.**

**Full chain, summarised:**

```
per-document extracted JSON (raw_pages field, one per PDF page)
        │  [upstream extraction — owned by Electronic_Supplement_A1, not this file]
        ▼
build_input_from_extracted.py
        │  validates page/word counts, joins pages with "\n\n", .strip()s,
        │  wraps in DOC_ID/FILENAME/PAGES/EXTRACTED_WORDS header — no lexical
        │  cleaning beyond whitespace join+strip; cleaned_words/normalized_tokens/
        │  reference_removed from the LDA-side manifest are NOT used here
        ▼
all_extracted_text_65docs.txt   (concatenation of all 65 documents)
        │
        ▼
run_rules_stage1.py
        │  parse_documents() + analyse_document() (§§2–5 above, unmodified
        │  rule-logic file) + evidence_score (§6)
        ▼
document_evidence_65.json  /  document_evidence_table_65.csv  /  manifest_65.json
        (OUTPUT of the deterministic rules — this is what §2's final-synthesis
        top-20 metadata and §2's batch digests, per 02_prompts_and_configuration.md,
        are themselves built from downstream)
```

**PDF→text extraction itself (Step 1's own production) remains owned by
`Electronic_Supplement_A1`** (see its own README and
`tables/extraction_page_audit.csv`, `tables/normalization_map.csv`) — this
Qwen supplement reuses that already-extracted `raw_pages` text as an input
and does not re-derive or duplicate its own PDF-extraction rules. This
division is the same one `qwen_65docs/review/01_input_content_audit.md`
already establishes; it is restated here only so a reader of this file
alone does not assume PDF extraction is covered by these deterministic
rules.

## 8. Version/record status

Everything in §§2–7 is confirmed directly against the source code this
round (not carried forward from an earlier description without
re-verification); §2's counts were computed programmatically, and §7's
chain was traced by reading both scripts' actual code, not restated from a
prior summary. What is **not independently re-verified in this round** (and
is flagged as such, not silently assumed correct): whether the per-document
extracted-text JSON files themselves (Step 1 of §7) are current/unmodified
since their own creation — that check belongs to the LDA supplement's own
provenance record, not this one.
