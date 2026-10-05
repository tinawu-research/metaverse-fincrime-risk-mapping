"""Reproducible PDF-to-LDA analysis for the 65-publication metaverse/cryptocurrency study.

Use the accompanying README.md, run_config.json and requirements-resolved.txt.
The analytical implementation is pipeline version 1.0.1.
"""
from __future__ import annotations

import os
# Colab sets an inline notebook backend in the parent process. This standalone
# analysis environment renders files, so select Agg BEFORE importing matplotlib.
os.environ['MPLBACKEND'] = 'Agg'
for _key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(_key, '1')
os.environ.setdefault('MPLCONFIGDIR', os.path.join(os.getcwd(), 'work', 'matplotlib_cache'))
import argparse
import csv
import hashlib
import importlib.metadata as im
import itertools
import json
import math
import platform
import re
import sys
import time
import unicodedata
import warnings
import zipfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import pymupdf
from gensim.corpora import Dictionary
from gensim.models import CoherenceModel, Phrases
from nltk.stem import WordNetLemmatizer
from pypdf import PdfReader
from scipy import sparse
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics import adjusted_rand_score, cohen_kappa_score
from sklearn.model_selection import GroupKFold
from sklearn.metrics.pairwise import cosine_similarity
from threadpoolctl import threadpool_limits

VERSION = '1.0.1'
REVIEW_URL = 'tables/reviewer_response_crosswalk.csv'
PACKAGES = ['pymupdf','pypdf','numpy','scipy','pandas','scikit-learn','gensim',
            'matplotlib','networkx','nltk','pyLDAvis','joblib','threadpoolctl']


@dataclass
class Config:
    input_dir: str = '/content/pdfs'
    output_dir: str = '/content/lda_results'
    profile: str = 'research'  # smoke tests plumbing; research supports reporting.
    k_values: tuple = tuple(range(2, 13))
    seeds: tuple = (11, 42, 97, 2026, 31415)
    folds: int = 3
    split_seed: int = 20260915
    max_iter: int = 250             # outer EM updates, with a bound trace at every update
    max_doc_update_iter: int = 250  # separate inner document inference cap
    perp_tol: float = 0.1           # absolute successive training perplexity difference
    mean_change_tol: float = 0.001
    alpha: float | None = None      # None = 1/K; total document prior concentration = 1
    eta: float = 0.01
    unit: str = 'chunk'             # chunk or document; original PDFs define validation groups
    chunk_size: int = 400           # normalized tokens; no overlap; never crosses PDFs
    min_tail: int = 100             # merge a shorter final tail into preceding chunk
    max_train_chunks_per_doc: int | None = 50  # evenly spaced, without replacement
    min_document_tokens: int = 100
    min_df: int = 2                 # counts ORIGINAL PDFs, not chunks
    max_df: float = 1.0
    max_features: int = 10000
    learned_phrases: bool = True
    phrase_min_count: int = 10
    phrase_threshold: float = 10.0
    lemmatize: bool = True          # WordNet noun lookup, no blind stemming
    strip_references: bool = True
    reference_min_fraction: float = 0.40
    near_duplicate_threshold: float = 0.93
    coherence_topn: int = 10
    coherence_tolerance: float = 0.02
    minimum_stability: float = 0.70  # declared heuristic, not a universal validity threshold
    minimum_diversity: float = 0.60
    minimum_converged_fraction: float = 0.80
    final_k_override: int | None = None
    final_k_reason: str = ''
    bootstrap_replicates: int = 2000
    network_terms: int = 40
    network_min_docs: int = 3
    network_min_jaccard: float = 0.05
    network_min_npmi: float = 0.05
    network_max_df: float = 0.90    # ubiquitous terms carry little document-level association information
    network_max_edges: int = 150
    run_sensitivity: bool = True
    enable_ocr: bool = False
    ocr_language: str = 'eng'
    metadata_csv: str = ''
    page_rules_csv: str = ''
    extra_stopwords: tuple = ()

    def checked(self):
        if self.profile == 'smoke':
            self.k_values = (2, 7, 8)
            self.seeds = (11, 42)
            self.folds = 2
            self.max_iter = 12
            self.max_doc_update_iter = 60
            self.bootstrap_replicates = 200
        if self.unit not in ('document','chunk') or self.folds < 2 or len(self.seeds) < 2:
            raise ValueError('Use document/chunk, at least two folds and two seeds.')
        if len(set(self.seeds)) != len(self.seeds) or len(set(self.k_values)) != len(self.k_values):
            raise ValueError('Seeds and K values must be unique.')
        if any(k < 2 for k in self.k_values) or self.chunk_size < self.min_tail:
            raise ValueError('K must be >=2 and chunk_size >= min_tail.')
        if self.final_k_override is not None and (self.final_k_override not in self.k_values or not self.final_k_reason.strip()):
            raise ValueError('A final K override must be evaluated in k_values and have a written reason.')
        return self


# Fixed lexical equivalents are declared BEFORE any fitting. They do not prescribe topics.
# Ambiguous abbreviations (ML, TF, IP, AR) are intentionally not expanded globally.
DOMAIN_ALIASES = {
    'non fungible tokens':'nft', 'non fungible token':'nft',
    'nonfungible tokens':'nft', 'nonfungible token':'nft', 'nfts':'nft',
    'cryptocurrencies':'cryptocurrency', 'crypto currencies':'cryptocurrency',
    'crypto currency':'cryptocurrency', 'cryptoassets':'cryptoasset',
    'crypto assets':'cryptoasset', 'crypto asset':'cryptoasset',
    'block chain':'blockchain', 'blockchains':'blockchain', 'metaverses':'metaverse',
    'smart contracts':'smart_contract', 'smart contract':'smart_contract',
    'decentralized finance':'defi', 'decentralised finance':'defi',
    'decentralized autonomous organizations':'dao', 'decentralised autonomous organisations':'dao',
    'decentralized autonomous organization':'dao', 'decentralised autonomous organisation':'dao', 'daos':'dao',
    'virtual reality':'virtual_reality', 'augmented reality':'augmented_reality',
    'mixed reality':'mixed_reality', 'extended reality':'extended_reality',
    'artificial intelligence':'artificial_intelligence', 'machine learning':'machine_learning',
    'deep learning':'deep_learning', 'generative ai':'generative_ai',
    'federated learning':'federated_learning', 'digital twins':'digital_twin', 'digital twin':'digital_twin',
    'digital assets':'digital_asset', 'digital asset':'digital_asset',
    'digital identities':'digital_identity', 'digital identity':'digital_identity',
    'identity theft':'identity_theft', 'identity impersonation':'identity_impersonation',
    'access control':'access_control', 'attribute based encryption':'attribute_based_encryption',
    'self sovereign identity':'self_sovereign_identity', 'self sovereign ai':'self_sovereign_ai',
    'zero knowledge proofs':'zero_knowledge_proof', 'zero knowledge proof':'zero_knowledge_proof',
    'post quantum':'post_quantum', 'quantum computing':'quantum_computing',
    'money laundering':'money_laundering', 'terrorist financing':'terrorist_financing',
    'terrorism financing':'terrorist_financing', 'financial crime':'financial_crime',
    'financial crimes':'financial_crime', 'financial fraud':'financial_fraud',
    'wash trading':'wash_trading', 'market manipulation':'market_manipulation',
    'insider trading':'insider_trading', 'tax evasion':'tax_evasion',
    'rug pulls':'rug_pull', 'rug pull':'rug_pull', 'ponzi schemes':'ponzi_scheme', 'ponzi scheme':'ponzi_scheme',
    'social engineering':'social_engineering', 'consumer protection':'consumer_protection',
    'consumer rights':'consumer_right', 'intellectual property':'intellectual_property',
    'data protection':'data_protection', 'data privacy':'data_privacy',
    'virtual worlds':'virtual_world', 'virtual world':'virtual_world',
    'real estate':'real_estate', 'atomic swaps':'atomic_swap', 'atomic swap':'atomic_swap',
    'cross chain':'cross_chain', 'cross metaverse':'cross_metaverse',
    'proof of personhood':'proof_of_personhood', 'sybil attacks':'sybil_attack', 'sybil attack':'sybil_attack',
    'cyber security':'cybersecurity', 'cyber crimes':'cybercrime', 'cyber crime':'cybercrime',
    'cybercrimes':'cybercrime', 'deep fakes':'deepfake', 'deepfakes':'deepfake',
    'web 3.0':'web3', 'web 3':'web3', 'decentralised':'decentralized',
    'normalised':'normalized', 'behaviour':'behavior', 'behaviours':'behavior',
}
MODEL_BOILERPLATE = {'doi','isbn','issn','copyright','sciencedirect','elsevier',
    'springer','ieee','et','al','fig','figure','figures','table','tables','vol',
    'pp','www','http','https','com','org','edu','author','authors','rights','reserved',
    'abstract','keywords','references','bibliography','received','accepted','published'}
DISPLAY_STOPWORDS = {'paper','study','research','analysis','result','based','using','use',
    'approach','model','method','proposed','propose','proposes','new','different','also',
    'metaverse','blockchain','technology','system','application','include','provide',
    'used','can','may','will','one','two','et','al','article','work','appendix','section',
    'issue','potential','like','various','however','therefore','time','address','challenge',
    'framework','future','development','environment','mention','process','information',
    'digital','virtual','blockchain_technology','metaverse_technology'}


def write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    def convert(x):
        if isinstance(x, (np.integer,np.floating)): return x.item()
        if isinstance(x, np.ndarray): return x.tolist()
        if isinstance(x, Path): return str(x)
        raise TypeError(type(x).__name__)
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=convert), encoding='utf-8')


def table(rows, path, columns=None):
    df = rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows,columns=columns)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path,index=False,encoding='utf-8-sig')
    return df


def slug(text):
    return re.sub(r'[^a-zA-Z0-9_-]+','_',str(text)).strip('_')[:100]


def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,default=str).encode()).hexdigest()


def save_plot(fig, directory, name):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    fig.tight_layout()
    fig.savefig(directory/(name+'.png'),dpi=300,bbox_inches='tight')
    fig.savefig(directory/(name+'.svg'),bbox_inches='tight')
    fig.savefig(directory/(name+'.pdf'),bbox_inches='tight')
    plt.close(fig)


def setup_resources(out, cfg):
    import nltk
    path=Path(out)/'private'/'nltk_data'; path.mkdir(parents=True,exist_ok=True)
    nltk.data.path.insert(0,str(path))
    if cfg.lemmatize:
        try: WordNetLemmatizer().lemmatize('wallets')
        except LookupError:
            if not nltk.download('wordnet',download_dir=str(path),quiet=True,raise_on_error=True):
                raise RuntimeError('WordNet download failed. Restore network access, or explicitly set lemmatize=False and document the change.')
            WordNetLemmatizer().lemmatize('wallets')
        from nltk.corpus import wordnet
        write_json(Path(out)/'tables'/'nlp_resource_version.json',{'wordnet':wordnet.get_version(),
            'lemmatizer':'WordNetLemmatizer; noun POS; domain aliases applied first'})


def clean_unicode(text):
    text=unicodedata.normalize('NFKC',text).replace('\u00ad','')
    text=re.sub(r'(?<=[A-Za-z])-\s*\n\s*(?=[a-z])','',text)
    return text


def extract_pdf(path, cfg):
    """Local extraction. Block order preserves within-paragraph phrase context.
    PyMuPDF restores word spacing in the supplied MetaRepo PDF; pypdf is fallback.
    OCR is optional and logged, never silently treated as identical extraction.
    """
    pages=[]; audits=[]
    try:
        with pymupdf.open(path) as pdf:
            if pdf.needs_pass: raise ValueError('Password-protected PDF')
            for index,page in enumerate(pdf):
                text='\n'.join(b[4] for b in page.get_text('blocks',sort=True) if b[6]==0)
                method='pymupdf_blocks'
                words=re.findall(r'[A-Za-z]+',text)
                image_area=sum(pymupdf.Rect(x['bbox']).get_area() for x in page.get_image_info())
                image_fraction=min(1.0,image_area/max(1,page.rect.get_area()))
                probable_scan=len(words)<30 and image_fraction>0.65
                if probable_scan and cfg.enable_ocr:
                    tp=page.get_textpage_ocr(language=cfg.ocr_language,dpi=300,full=True)
                    text=page.get_text(textpage=tp); method='tesseract_ocr'
                text=clean_unicode(text); pages.append(text)
                audits.append({'page':index+1,'method':method,'characters':len(text),
                    'word_count':len(text.split()),'image_fraction':image_fraction,
                    'probable_scan':probable_scan,'low_text':len(words)<30})
    except Exception as first_error:
        if cfg.enable_ocr: raise RuntimeError(f'Extraction/OCR failed for {path.name}: {first_error}') from first_error
        reader=PdfReader(path)
        pages=[clean_unicode(p.extract_text() or '') for p in reader.pages]
        audits=[{'page':i+1,'method':'pypdf_fallback','characters':len(t),'word_count':len(t.split()),
                 'fallback_reason':str(first_error),'low_text':len(t.split())<30} for i,t in enumerate(pages)]
    return pages,audits


def strip_pages(pages, cfg, rule=None):
    """Return (physical page number, cleaned text) with a complete action log."""
    rule=rule or {}; actions=[]
    start=int(rule.get('first_page') or 1); end=int(rule.get('last_page') or len(pages))
    if not 1<=start<=end<=len(pages): raise ValueError(f'Invalid physical page range {start}:{end}')
    retained=[]
    for i,t in enumerate(pages,1):
        if not start<=i<=end:
            actions.append({'page':i,'action':'page_rule_exclusion','reason':rule.get('reason','')}); continue
        if sum(s in t.lower() for s in ('rapid #','lender:','borrower:','cross ref id'))>=2:
            actions.append({'page':i,'action':'library_delivery_cover'}); continue
        retained.append((i,t))
    candidates=Counter()
    for _,t in retained:
        lines=[x.strip() for x in t.splitlines() if x.strip()]
        candidates.update(set(x for x in lines[:2]+lines[-2:] if len(x)<150))
    repeated={x for x,n in candidates.items() if n>=max(3,math.ceil(len(retained)*.4))}
    result=[]
    for p,t in retained:
        lines=[]
        for line in t.splitlines():
            line=line.strip()
            if line in repeated or re.fullmatch(r'\d{1,5}',line or ' '):
                if line: actions.append({'page':p,'action':'repeated_margin_or_page_number','text':line})
            else: lines.append(line)
        result.append((p,'\n'.join(lines)))
    total=sum(len(t) for _,t in result); consumed=0; stopped=False; trimmed=[]
    for p,t in result:
        keep=[]
        for line in t.splitlines():
            heading=re.sub(r'^[\dIVXivx.\s]+','',line.strip())
            heading=re.sub(r'\s+','',heading).lower().rstrip(':')
            if cfg.strip_references and heading in ('references','bibliography','workscited') and consumed/max(total,1)>=cfg.reference_min_fraction:
                actions.append({'page':p,'action':'reference_cut','heading':line,
                    'fraction_of_clean_text':consumed/max(total,1)}); stopped=True; break
            keep.append(line); consumed+=len(line)+1
        trimmed.append((p,'\n'.join(keep)))
        if stopped: break
    actions.append({'action':'reference_status','removed':stopped,
                    'rule':f'standalone heading after {cfg.reference_min_fraction:.0%} of text'})
    return trimmed,actions


def normalize_pages(pages, cfg):
    stops=set(ENGLISH_STOP_WORDS)|MODEL_BOILERPLATE|set(cfg.extra_stopwords)
    aliases=sorted(DOMAIN_ALIASES,key=len,reverse=True)
    pattern=re.compile(r'(?<![a-z0-9_])('+ '|'.join(re.escape(x) for x in aliases)+r')(?![a-z0-9_])')
    lemma=WordNetLemmatizer(); audit=Counter(); output=[]
    for page,text in pages:
        t=clean_unicode(text).lower()
        t=re.sub(r'https?://\S+|www\.\S+|\b\S+@\S+\b',' ',t)
        t=re.sub(r'10\.\d{4,9}/\S+',' ',t)
        t=re.sub(r'[\u2010-\u2015-]',' ',t)
        t=re.sub(r'[^a-z0-9_\s.]',' ',t); t=re.sub(r'\s+',' ',t)
        def sub(m):
            src=m.group(); dest=DOMAIN_ALIASES[src]
            audit[(src,dest,'domain_alias')]+=1
            return dest
        t=pattern.sub(sub,t)
        tokens=[]; previous=None
        for token in re.findall(r'[a-z][a-z0-9_]*',t):
            if len(token)<3 or len(token)>35 or token in stops: continue
            canonical=lemma.lemmatize(token,pos='n') if cfg.lemmatize and '_' not in token else token
            if canonical!=token: audit[(token,canonical,'wordnet_noun')]+=1
            if canonical in stops: continue
            if canonical==previous:
                audit[(token,canonical,'adjacent_duplicate_removed')]+=1; continue
            tokens.append(canonical); previous=canonical
        output.append((page,tokens))
    return output,audit


def load_page_rules(cfg):
    # Exact content hashes make the packaged override safe if a PDF is renamed.
    builtin=globals().get('CORPUS_PAGE_RULES',{})
    rules=dict(builtin)
    if cfg.page_rules_csv:
        for row in pd.read_csv(cfg.page_rules_csv).fillna('').to_dict('records'):
            key=row.get('sha256') or row.get('relative_path')
            if key: rules[str(key)]=row
    return rules


def audit_corpus(cfg, out):
    source=Path(cfg.input_dir).expanduser().resolve()
    files=sorted((p for p in source.rglob('*') if p.is_file() and p.suffix.lower()=='.pdf'),key=lambda p:p.relative_to(source).as_posix().lower())
    if not files: raise FileNotFoundError(f'No PDFs in {source}. Upload/extract the corpus or set the Drive folder.')
    docs=[]; records=[]; page_rows=[]; cleaning=[]; normalization=Counter(); seen_sha={}; seen_body={}; failures=[]
    rules=load_page_rules(cfg)
    for i,path in enumerate(files,1):
        relative=path.relative_to(source).as_posix(); sha=hashlib.sha256(path.read_bytes()).hexdigest()
        doc_id='D'+sha[:12]; row={'document_id':doc_id,'relative_path':relative,'filename':path.name,'sha256':sha,'status':'pending'}
        if sha in seen_sha:
            row.update(status='exact_file_duplicate',duplicate_of=seen_sha[sha]); records.append(row); continue
        seen_sha[sha]=doc_id
        try:
            raw,pages_audit=extract_pdf(path,cfg)
            for r in pages_audit: page_rows.append(dict(document_id=doc_id,**r))
            rule=rules.get(sha,rules.get(relative,{}))
            clean,actions=strip_pages(raw,cfg,rule)
            for action in actions: cleaning.append(dict(document_id=doc_id,**action))
            body='\n'.join(t for _,t in clean)
            body_hash=hashlib.sha256(re.sub(r'\s+','',body.lower()).encode()).hexdigest()
            norm,audit=normalize_pages(clean,cfg)
            tokens=[w for _,ws in norm for w in ws]
            row.update(page_count=len(raw),raw_words=sum(len(t.split()) for t in raw),
                cleaned_words=len(body.split()),normalized_tokens=len(tokens),body_hash=body_hash,
                reference_removed=any(x['action']=='reference_cut' for x in actions),
                extraction_review_flag=any(x.get('probable_scan') for x in pages_audit),
                long_word_fraction=float(np.mean([len(x)>25 for x in body.split()])) if body.split() else 1.0)
            if len(tokens)<cfg.min_document_tokens:
                raise ValueError(f'Only {len(tokens)} usable tokens: check extraction/OCR; no silent exclusion')
            if body_hash in seen_body:
                row.update(status='exact_body_duplicate',duplicate_of=seen_body[body_hash]); records.append(row); continue
            seen_body[body_hash]=doc_id
            row['status']='included'; records.append(row); normalization.update(audit)
            docs.append({'id':doc_id,'filename':path.name,'relative_path':relative,'sha256':sha,
                         'pages':clean,'normalized_pages':norm,'tokens':tokens,'text':body,'group':doc_id})
            private=out/'private'/'extracted'; private.mkdir(parents=True,exist_ok=True)
            write_json(private/(doc_id+'.json'),{'raw_pages':raw,'cleaned_pages':clean,'normalization':norm})
        except Exception as e:
            row.update(status='error',error=str(e)); records.append(row); failures.append(row)
        print(f'PDF {i}/{len(files)}: {path.name}: {row["status"]}',flush=True)
    manifest=table(records,out/'tables'/'corpus_manifest.csv')
    table(page_rows,out/'tables'/'extraction_page_audit.csv')
    table(cleaning,out/'private'/'cleaning_actions.csv')
    table([dict(original_form=a,normalized_form=b,mapping_type=c,count=n) for (a,b,c),n in normalization.items()],out/'tables'/'normalization_map.csv')
    write_json(out/'tables'/'corpus_flow.json',{'files_discovered':len(files),'included':len(docs),
        'exact_file_duplicates':sum(x['status']=='exact_file_duplicate' for x in records),
        'exact_body_duplicates':sum(x['status']=='exact_body_duplicate' for x in records),
        'errors':len(failures),'screening_prisma':'Not reconstructed from this folder; use the separate screening record.'})
    if failures: raise RuntimeError('Extraction failed; see corpus_manifest.csv. Fix the listed PDFs before rerunning.')
    if len(docs)<max(12,2*max(cfg.k_values)):
        warnings.warn(f'Only {len(docs)} articles for K up to {max(cfg.k_values)}. Exploratory results may be weak.')
    # Near matches are retained and grouped for validation, not silently deduplicated.
    tf=TfidfVectorizer(analyzer='char_wb',ngram_range=(5,5),min_df=2,max_features=40000).fit_transform([d['text'] for d in docs])
    sims=cosine_similarity(tf); parent=list(range(len(docs)))
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    pairs=[]
    for a,b in itertools.combinations(range(len(docs)),2):
        if sims[a,b]>=cfg.near_duplicate_threshold:
            pairs.append({'document_a':docs[a]['id'],'document_b':docs[b]['id'],'cosine_char5':sims[a,b],
                          'decision':'retained; same validation group; human publication-identity check pending'})
            parent[find(b)]=find(a)
    for i,d in enumerate(docs): d['group']=docs[find(i)]['id']
    table(pairs,out/'tables'/'near_duplicate_candidates.csv',columns=['document_a','document_b','cosine_char5','decision'])
    table([{'document_id':d['id'],'filename':d['filename'],'publication_type':'unknown','type_verified':False,
        'year':'','screening_id':'','quality_appraisal_tool':'','quality_appraisal_result':'','notes':''} for d in docs],out/'tables'/'metadata_template.csv')
    return docs,manifest


def fit_representation(docs,cfg):
    # Only training PDFs are passed here during cross-validation.
    sentences=[ws for d in docs for _,ws in d['normalized_pages'] if ws]
    phraser=Phrases(sentences,min_count=cfg.phrase_min_count,threshold=cfg.phrase_threshold,delimiter='_').freeze() if cfg.learned_phrases else None
    texts=[[w for _,ws in d['normalized_pages'] for w in (phraser[ws] if phraser else ws)] for d in docs]
    dictionary=Dictionary(texts)
    dictionary.filter_extremes(no_below=cfg.min_df,no_above=cfg.max_df,keep_n=cfg.max_features)
    dictionary.compactify()
    if len(dictionary)<max(30,2*max(cfg.k_values)): raise ValueError('Vocabulary too small. Inspect preprocessing and document-frequency limits.')
    return {'phraser':phraser,'dictionary':dictionary}


def chunk_spans(n,size,min_tail):
    if n==0: return []
    spans=[(i,min(i+size,n)) for i in range(0,n,size)]
    if len(spans)>1 and spans[-1][1]-spans[-1][0]<min_tail:
        spans[-2]=(spans[-2][0],spans[-1][1]); spans.pop()
    return spans


def make_units(docs,rep,cfg):
    dictionary=rep['dictionary']; phraser=rep['phraser']
    units=[]; bows=[]; texts=[]; coverage=[]
    for d in docs:
        words=[]; locations=[]
        for p,ws in d['normalized_pages']:
            transformed=list(phraser[ws]) if phraser else ws
            words.extend(transformed); locations.extend([p]*len(transformed))
        texts.append([w for w in words if w in dictionary.token2id])
        known=sum(w in dictionary.token2id for w in words)
        coverage.append({'document_id':d['id'],'tokens_before_vocabulary':len(words),'in_vocabulary_tokens':known,
                         'oov_fraction':1-known/max(1,len(words))})
        spans=[(0,len(words))] if cfg.unit=='document' else chunk_spans(len(words),cfg.chunk_size,cfg.min_tail)
        for j,(start,end) in enumerate(spans):
            bow=dictionary.doc2bow(words[start:end])
            if not bow: raise ValueError(f'Empty vocabulary unit in {d["filename"]}. Adjust preprocessing; no silent drop.')
            units.append({'document_id':d['id'],'unit_index':j,'start_token':start,'end_token':end,
                'page_start':locations[start],'page_end':locations[end-1],'token_count':sum(v for _,v in bow),
                'normalized_excerpt':' '.join(words[start:min(end,start+180)])})
            bows.append(bow)
    rr=[]; cc=[]; vv=[]
    for i,bow in enumerate(bows):
        for j,v in bow: rr.append(i); cc.append(j); vv.append(v)
    X=sparse.csr_matrix((vv,(rr,cc)),shape=(len(bows),len(dictionary)),dtype=np.float64)
    selected=[]
    for d in docs:
        ix=[i for i,u in enumerate(units) if u['document_id']==d['id']]
        cap=cfg.max_train_chunks_per_doc
        if cfg.unit=='chunk' and cap is not None and len(ix)>cap:
            ix=[ix[k] for k in np.linspace(0,len(ix)-1,cap,dtype=int)]
        selected.extend(ix)
    return {'X':X,'units':units,'training_indices':np.array(selected,dtype=int),'texts':texts,'coverage':coverage}


class TracedLDA(LatentDirichletAllocation):
    """Observe sklearn 1.7.2's own training evaluations, without changing updates.
    Its private hook is version checked and tested; no score(X) calls are added
    inside EM. n_iter_ has a stopping-edge convention, so count EM calls directly.
    """
    def fit(self,X,y=None):
        if im.version('scikit-learn')!='1.7.2':
            raise RuntimeError('Install scikit-learn==1.7.2 for the tested convergence-trace hook.')
        self.trace_=[]; self.actual_iterations_=0; self._record_trace=True
        try: super().fit(X,y)
        finally: self._record_trace=False
        self.converged_=len(self.trace_)>=2 and abs(self.trace_[-1]['perplexity']-self.trace_[-2]['perplexity'])<self.perp_tol
        return self

    def _em_step(self,X,total_samples,batch_update,parallel=None):
        self.actual_iterations_+=1
        return super()._em_step(X,total_samples,batch_update,parallel)

    def _perplexity_precomp_distr(self,X,doc_topic_distr=None,sub_sampling=False):
        value=super()._perplexity_precomp_distr(X,doc_topic_distr,sub_sampling)
        if getattr(self,'_record_trace',False):
            row={'iteration':self.actual_iterations_,'perplexity':float(value),
                 'variational_bound':float(-np.log(value)*X.sum()),'bound_per_token':float(-np.log(value))}
            if self.trace_ and self.trace_[-1]['iteration']==self.actual_iterations_: self.trace_[-1]=row
            else: self.trace_.append(row)
        return value


def fit_model(X,k,seed,cfg,cache):
    cache=Path(cache)
    if cache.exists():
        try: return joblib.load(cache)
        except Exception as e:
            print(f'Unreadable checkpoint {cache.name}; refitting ({type(e).__name__}).',flush=True)
    model=TracedLDA(n_components=k,doc_topic_prior=cfg.alpha,topic_word_prior=cfg.eta,
        learning_method='batch',max_iter=cfg.max_iter,max_doc_update_iter=cfg.max_doc_update_iter,
        evaluate_every=1,perp_tol=cfg.perp_tol,mean_change_tol=cfg.mean_change_tol,n_jobs=1,random_state=int(seed))
    before=time.time()
    with threadpool_limits(limits=1): model.fit(X)
    model.elapsed_seconds_=time.time()-before
    cache.parent.mkdir(parents=True,exist_ok=True)
    temporary=cache.with_name(cache.name+'.tmp')
    joblib.dump(model,temporary)
    temporary.replace(cache)  # promote only a fully written model
    return model


def phi(model):
    return model.components_/model.components_.sum(axis=1,keepdims=True)


def top_terms(model,dictionary,n=10):
    return [[dictionary[int(i)] for i in row.argsort()[::-1][:n]] for row in phi(model)]


def aggregate_documents(theta,units,ids,weighted=True):
    answer=[]
    for doc_id in ids:
        mask=np.array([u['document_id']==doc_id for u in units])
        weights=np.array([u['token_count'] for u in units])[mask] if weighted else None
        answer.append(np.average(theta[mask],axis=0,weights=weights))
    a=np.array(answer); return a/a.sum(axis=1,keepdims=True)


def match_topics(A,B,topn=10):
    # sqrt(JS divergence base 2) is in [0,1]; similarity is one minus distance.
    distance=cdist(A,B,metric=lambda x,y: float(np.sqrt(max(0,0.5*np.sum(x*np.log2(x/((x+y)/2)))+0.5*np.sum(y*np.log2(y/((x+y)/2)))))))
    rows,cols=linear_sum_assignment(distance)
    jacc=[]
    for a,b in zip(rows,cols):
        sa=set(A[a].argsort()[-topn:]); sb=set(B[b].argsort()[-topn:]); jacc.append(len(sa&sb)/len(sa|sb))
    return rows,cols,1-distance[rows,cols],np.array(jacc)


def seed_stability(models,data,doc_ids):
    phis=[phi(m) for m in models]
    doc_theta=[aggregate_documents(m.transform(data['X']),data['units'],doc_ids) for m in models]
    pairs=[]; sums=np.zeros(len(models))
    for a,b in itertools.combinations(range(len(models)),2):
        rows,cols,js,jacc=match_topics(phis[a],phis[b]); score=float(js.mean()); sums[a]+=score; sums[b]+=score
        aligned=doc_theta[b][:,cols]
        pairs.append({'seed_a':models[a].random_state,'seed_b':models[b].random_state,
            'matched_js_similarity':score,'matched_top10_jaccard':float(jacc.mean()),
            'dominant_topic_ari':adjusted_rand_score(doc_theta[a].argmax(1),doc_theta[b].argmax(1)),
            'document_topic_mean_l1':float(np.abs(doc_theta[a][:,rows]-aligned).sum(1).mean())})
    medoid=int(np.argmax(sums)) # deterministic order resolves a tie; never choose maximum coherence seed
    return pairs,medoid


def split_completion(X,seed):
    rng=np.random.default_rng(seed); observed=X.copy(); target=X.copy()
    observed.data=rng.binomial(X.data.astype(np.int64),.5).astype(float)
    target.data=X.data-observed.data; observed.eliminate_zeros(); target.eliminate_zeros()
    # Zero halves are possible for very short units; fail visibly instead of leaking held-out words.
    if np.any(np.asarray(observed.sum(1)).ravel()==0) or np.any(np.asarray(target.sum(1)).ravel()==0):
        raise ValueError('A completion half is empty. Increase chunk size or inspect very sparse documents.')
    assert (observed+target-X).nnz==0
    return observed,target


def completion_scores(model,observed,target,unigram,units):
    theta=model.transform(observed); topics=phi(model); rows=[]
    for i in range(target.shape[0]):
        row=target.getrow(i); prob=theta[i]@topics[:,row.indices]
        ll=float(row.data@np.log(np.maximum(prob,1e-300)))
        baseline=float(row.data@np.log(unigram[row.indices]))
        rows.append({'document_id':units[i]['document_id'],'unit_index':units[i]['unit_index'],
                     'completion_log_likelihood':ll,'unigram_log_likelihood':baseline,'heldout_tokens':float(row.sum())})
    docs=pd.DataFrame(rows).groupby('document_id',as_index=False)[['completion_log_likelihood','unigram_log_likelihood','heldout_tokens']].sum()
    docs['log_likelihood_per_token']=docs.completion_log_likelihood/docs.heldout_tokens
    docs['unigram_per_token']=docs.unigram_log_likelihood/docs.heldout_tokens
    docs['gain_vs_unigram_nats']=docs.log_likelihood_per_token-docs.unigram_per_token
    summary={'validation_macro_loglik_per_token':float(docs.log_likelihood_per_token.mean()),
        'validation_completion_perplexity':float(np.exp(-docs.log_likelihood_per_token.mean())),
        'validation_total_completion_loglik':float(docs.completion_log_likelihood.sum()),
        'validation_micro_loglik_per_token':float(docs.completion_log_likelihood.sum()/docs.heldout_tokens.sum()),
        'validation_gain_vs_unigram_nats':float(docs.gain_vs_unigram_nats.mean())}
    return summary,docs


def batch_coherence(models,texts,dictionary,topn):
    lists=[top_terms(m,dictionary,topn) for m in models]; scores=[{} for _ in models]
    for metric,window in [('c_v',110),('c_npmi',10)]:
        cm=CoherenceModel.for_topics(lists,texts=texts,dictionary=dictionary,coherence=metric,window_size=window,processes=1,topn=topn)
        for result,topics in zip(scores,lists):
            cm.topics=topics
            values=np.array(cm.get_coherence_per_topic(),dtype=float)
            result[metric]=float(np.mean(values)); result[metric+'_per_topic']=values.tolist()
    for result,topics in zip(scores,lists):
        result['topic_diversity']=len(set(itertools.chain.from_iterable(topics)))/sum(map(len,topics))
    return scores


# Verified physical PDF pages: the first seven pages are delivery/book front matter.
# The filename says Cryptocurrency; the actual chapter title says Cryptography.
CORPUS_PAGE_RULES = {
    'f993b1e11c98058f5746d549a0dfd6f94ec92340d5b178bc024f2aacbf2f3029': {
        'first_page':8,'last_page':50,
        'reason':'Chapter 14, Cryptography in the metaverse: advanced protocols for secure communication; remove delivery sheet and book front matter.'}
}


def cross_validate(docs,cfg,out):
    groups=[d['group'] for d in docs]
    if len(set(groups))<cfg.folds: raise ValueError('Too few independent document groups for requested folds.')
    splitter=GroupKFold(n_splits=cfg.folds,shuffle=True,random_state=cfg.split_seed)
    all_rows=[]; all_stability=[]; splits=[]; all_scores=[]; coverage=[]; traces=[]
    for fold,(tr,va) in enumerate(splitter.split(np.arange(len(docs)),groups=groups),1):
        train=[docs[i] for i in tr]; valid=[docs[i] for i in va]
        assert not ({d['group'] for d in train}&{d['group'] for d in valid})
        for part,subset in [('train',train),('validation',valid)]:
            splits.extend({'fold':fold,'part':part,'document_id':d['id'],'group':d['group']} for d in subset)
        rep=fit_representation(train,cfg); td=make_units(train,rep,cfg); vd=make_units(valid,rep,cfg)
        trainX=td['X'][td['training_indices']]
        observed,target=split_completion(vd['X'],cfg.split_seed+fold)
        unigram=np.asarray(trainX.sum(0)).ravel()+.5; unigram/=unigram.sum()
        coverage.extend(dict(fold=fold,**x) for x in vd['coverage'])
        vocabulary=rep['dictionary']
        write_json(out/'private'/f'fold_{fold}_vocabulary.json',vocabulary.token2id)
        fold_models=[]; fold_rows=[]; models_by_k={}
        for k in cfg.k_values:
            models=[]
            for seed in cfg.seeds:
                print(f'CV fold {fold}/{cfg.folds} | K={k} | seed={seed}',flush=True)
                model=fit_model(trainX,k,seed,cfg,out/'private'/'cache'/f'cv_f{fold}_k{k}_s{seed}.joblib')
                score,perdoc=completion_scores(model,observed,target,unigram,vd['units'])
                perdoc['fold']=fold; perdoc['k']=k; perdoc['seed']=seed
                all_scores.extend(perdoc.to_dict('records'))
                row=dict(fold=fold,k=k,seed=seed,train_documents=len(train),validation_documents=len(valid),
                    train_units=trainX.shape[0],vocabulary_size=trainX.shape[1],
                    alpha=model.doc_topic_prior_,eta=model.topic_word_prior_,
                    train_variational_bound=model.trace_[-1]['variational_bound'],
                    train_bound_per_token=model.trace_[-1]['bound_per_token'],
                    train_bound_perplexity=model.trace_[-1]['perplexity'],
                    iterations=model.actual_iterations_,converged=model.converged_,seconds=model.elapsed_seconds_,**score)
                fold_models.append(model); fold_rows.append(row); models.append(model)
                traces.extend(dict(fold=fold,k=k,seed=seed,**t) for t in model.trace_)
            pairs,_=seed_stability(models,td,[d['id'] for d in train])
            all_stability.extend(dict(fold=fold,k=k,**p) for p in pairs)
            models_by_k[k]=models
        print(f'CV fold {fold}: computing cached C_v and C_NPMI co-occurrences',flush=True)
        coherence=batch_coherence(fold_models,td['texts'],vocabulary,cfg.coherence_topn)
        for row,coh in zip(fold_rows,coherence):
            row.update({key:value for key,value in coh.items() if not key.endswith('_per_topic')})
        all_rows.extend(fold_rows)
        table(all_rows,out/'tables'/'model_selection_runs.csv')
        table(all_stability,out/'tables'/'seed_stability_cv.csv')
        table(traces,out/'tables'/'convergence_traces_cv.csv')
    table(splits,out/'tables'/'document_validation_splits.csv')
    table(all_scores,out/'tables'/'validation_document_completion.csv')
    table(coverage,out/'tables'/'validation_vocabulary_coverage.csv')
    runs=pd.DataFrame(all_rows); stability=pd.DataFrame(all_stability)
    summary=[]
    for k,g in runs.groupby('k'):
        row={'k':int(k),'runs':len(g),'converged_fraction':float(g.converged.mean())}
        for col in ['c_v','c_npmi','topic_diversity','validation_macro_loglik_per_token',
                    'validation_gain_vs_unigram_nats','train_bound_per_token','train_bound_perplexity']:
            fold_means=g.groupby('fold')[col].mean()
            row[col+'_mean']=float(fold_means.mean())
            row[col+'_fold_sd']=float(fold_means.std(ddof=1))
            row[col+'_fold_se']=float(fold_means.std(ddof=1)/np.sqrt(len(fold_means)))
            row[col+'_mean_seed_sd']=float(g.groupby('fold')[col].std(ddof=1).mean())
        sg=stability[stability.k==k]
        for col in ['matched_js_similarity','matched_top10_jaccard','dominant_topic_ari','document_topic_mean_l1']:
            row[col+'_mean']=float(sg[col].mean()); row[col+'_pair_sd']=float(sg[col].std(ddof=1))
        row['validation_completion_perplexity']=float(np.exp(-row['validation_macro_loglik_per_token_mean']))
        summary.append(row)
    summary=table(summary,out/'tables'/'model_selection_summary.csv')
    return summary,runs


def recommend_k(summary,cfg,out):
    s=summary.copy()
    needed=['c_v_mean','validation_macro_loglik_per_token_mean','matched_js_similarity_mean']
    if not np.isfinite(s[needed].to_numpy()).all():
        raise ValueError('Non-finite selection metrics. Inspect vocabulary/coherence and diagnostic runs.')
    best=s.loc[s.c_v_mean.idxmax()]
    tolerance=max(cfg.coherence_tolerance,float(best.c_v_fold_se))
    s['coherence_shortlist']=s.c_v_mean>=float(best.c_v_mean)-tolerance
    s['stability_gate']=s.matched_js_similarity_mean>=cfg.minimum_stability
    s['diversity_gate']=s.topic_diversity_mean>=cfg.minimum_diversity
    s['convergence_gate']=s.converged_fraction>=cfg.minimum_converged_fraction
    eligible=s[s.coherence_shortlist&s.stability_gate&s.diversity_gate&s.convergence_gate]
    gates_passed=not eligible.empty
    if eligible.empty: eligible=s[s.coherence_shortlist]
    predictive=eligible.loc[eligible.validation_macro_loglik_per_token_mean.idxmax()]
    cutoff=float(predictive.validation_macro_loglik_per_token_mean-predictive.validation_macro_loglik_per_token_fold_se)
    candidates=eligible[eligible.validation_macro_loglik_per_token_mean>=cutoff]
    recommended=int(candidates.k.min())
    chosen=cfg.final_k_override or recommended
    note=[]
    if not gates_passed: note.append('No coherence-shortlisted K passed all declared stability, diversity, and convergence gates. Recommendation is provisional; inspect and rerun before reporting.')
    if recommended in (min(cfg.k_values),max(cfg.k_values)): note.append('Recommendation lies at the tested K boundary; expand the range before claiming a resolved optimum.')
    if cfg.profile!='research': note.append('Smoke profile: validation only, not publication evidence or a substantive K recommendation.')
    note.append('Human interpretability checks by at least two coders remain pending until completed rating files are supplied.')
    decision={'recommended_k':recommended,'final_k':int(chosen),'tested_k':list(cfg.k_values),
        'gates_passed':gates_passed,'coherence_best_k':int(best.k),'coherence_tolerance_used':tolerance,
        'predictive_cutoff_nats_per_token':cutoff,'manual_override_reason':cfg.final_k_reason,
        'rule':'Shortlist within max(0.02, best-K fold SE) of best mean C_v; apply declared stability/diversity/convergence gates; retain candidates within one fold SE of best validation completion log score; choose smallest K. If gates fail, retain coherence shortlist and mark provisional.',
        'uncertainty_note':'Fold SE and dependent seed-pair SD are descriptive model-selection aids, not independent inferential confidence intervals.',
        'notes':note}
    table(s,out/'tables'/'model_selection_decision_table.csv')
    write_json(out/'model_selection_decision.json',decision)
    fig,axes=plt.subplots(2,3,figsize=(15,8))
    specs=[('c_v_mean','c_v_fold_sd','C_v coherence (fold SD)'),
           ('validation_completion_perplexity',None,'Validation completion perplexity'),
           ('matched_js_similarity_mean','matched_js_similarity_pair_sd','Matched topic stability (dependent pair SD)'),
           ('validation_macro_loglik_per_token_mean','validation_macro_loglik_per_token_fold_sd','Validation log score per token (fold SD)'),
           ('topic_diversity_mean',None,'Top-10 topic diversity'),('converged_fraction',None,'Converged runs / all runs')]
    for ax,(col,err,title) in zip(axes.flat,specs):
        ax.errorbar(s.k,s[col],yerr=s[err] if err else None,marker='o',capsize=3,color='#126782')
        ax.axvline(chosen,color='#c95e35',linestyle='--',label=f'K={chosen}')
        ax.set(title=title,xlabel='Number of topics (K)'); ax.set_xticks(s.k); ax.grid(alpha=.2)
    fig.suptitle('Model comparison before final fitting — '+('SMOKE TEST' if cfg.profile=='smoke' else 'document-grouped validation'))
    save_plot(fig,out/'figures','model_selection_diagnostics')
    return decision


def fit_final_candidates(docs,cfg,out,decision):
    rep=fit_representation(docs,cfg); data=make_units(docs,rep,cfg)
    chosen=decision['final_k']
    candidates=sorted({k for k in (chosen-1,chosen,chosen+1,7,8) if k in cfg.k_values})
    families={}; flat=[]; rows=[]; pair_rows=[]; traces=[]
    X=data['X'][data['training_indices']]
    for k in candidates:
        models=[]
        for seed in cfg.seeds:
            print(f'Final corpus | K={k} | seed={seed}',flush=True)
            m=fit_model(X,k,seed,cfg,out/'private'/'cache'/f'full_k{k}_s{seed}.joblib')
            models.append(m); flat.append(m)
            rows.append({'k':k,'seed':seed,'iterations':m.actual_iterations_,'converged':m.converged_,
                         'bound_per_token':m.trace_[-1]['bound_per_token'],'perplexity_bound':m.trace_[-1]['perplexity']})
            traces.extend(dict(k=k,seed=seed,**r) for r in m.trace_)
        pairs,medoid=seed_stability(models,data,[d['id'] for d in docs])
        pair_rows.extend(dict(k=k,**r) for r in pairs)
        families[k]={'models':models,'medoid':medoid,'model':models[medoid]}
    cohs=batch_coherence(flat,data['texts'],rep['dictionary'],cfg.coherence_topn)
    for row,coh in zip(rows,cohs):
        row.update({k:v for k,v in coh.items() if not k.endswith('_per_topic')})
    for m,coh in zip(flat,cohs): m.topic_coherence_=coh
    table(rows,out/'tables'/'full_corpus_seed_diagnostics.csv')
    table(pair_rows,out/'tables'/'full_corpus_seed_stability.csv')
    table(traces,out/'tables'/'convergence_traces_full_corpus.csv')
    table(data['coverage'],out/'tables'/'full_corpus_vocabulary_coverage.csv')
    table([{k:v for k,v in u.items() if k!='normalized_excerpt'} for u in data['units']],out/'tables'/'unit_manifest.csv')
    table(data['units'],out/'private'/'unit_manifest_with_passages.csv')
    rep['dictionary'].save(str(out/'private'/'dictionary.gensim'))
    if rep['phraser']: rep['phraser'].save(str(out/'private'/'phrases.gensim'))
    sparse.save_npz(out/'private'/'unit_term_counts.npz',data['X'])
    table([{'token_id':i,'term':rep['dictionary'][i],
        'document_frequency':rep['dictionary'].dfs.get(i,0)} for i in range(len(rep['dictionary']))],out/'tables'/'vocabulary.csv')
    phrase_counts=Counter(itertools.chain.from_iterable(data['texts']))
    phrase_rows=[{'phrase':term,'association_score':score,'corpus_occurrences':phrase_counts[term]}
        for term,score in rep['phraser'].phrasegrams.items()] if rep['phraser'] else []
    table(phrase_rows,out/'tables'/'learned_phrases.csv',columns=['phrase','association_score','corpus_occurrences'])
    model=families[chosen]['model']
    joblib.dump(model,out/'private'/'final_lda_model.joblib')
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    for m in families[chosen]['models']:
        trace=pd.DataFrame(m.trace_)
        axes[0].plot(trace.iteration,trace.bound_per_token,label=f'seed {m.random_state}')
        axes[1].plot(trace.iteration,trace.perplexity,label=f'seed {m.random_state}')
    axes[0].set(title='Training variational lower bound',xlabel='Actual outer EM update',ylabel='Bound per token (nats)')
    axes[1].set(title='Training bound-based perplexity',xlabel='Actual outer EM update',ylabel='Perplexity')
    for ax in axes: ax.legend(fontsize=8); ax.grid(alpha=.2)
    save_plot(fig,out/'figures','final_convergence_trace')
    return rep,data,families


def topic_word_tables(model,rep,prevalence,cfg):
    P=phi(model); dictionary=rep['dictionary']; background=prevalence@P
    summaries=[]; terms=[]
    for t,prob in enumerate(P):
        raw=prob.argsort()[::-1]
        pool=[int(i) for i in raw[:100] if dictionary[int(i)] not in DISPLAY_STOPWORDS]
        def score(i):
            term=dictionary[i]
            return .6*np.log(prob[i])+.4*np.log(prob[i]/background[i])+(.10 if '_' in term else 0)
        chosen=sorted(pool,key=lambda i:(-score(i),dictionary[i]))[:10]
        selected_mass=sum(prob[i] for i in chosen)
        label=' / '.join(dictionary[i].replace('_',' ') for i in chosen[:3])
        summaries.append({'topic':f'T{t+1:02d}','suggested_label':label,'label_status':'provisional; human interpretation pending',
            'raw_top10':', '.join(dictionary[int(i)] for i in raw[:10]),
            'display_top10':', '.join(dictionary[i] for i in chosen),'selected_probability_mass':selected_mass,
            'mean_document_prevalence':prevalence[t],
            'c_v':model.topic_coherence_['c_v_per_topic'][t],
            'c_npmi':model.topic_coherence_['c_npmi_per_topic'][t]})
        chosen_order={i:j+1 for j,i in enumerate(chosen)}
        for rank,i in enumerate(raw[:100],1):
            i=int(i)
            terms.append({'topic':f'T{t+1:02d}','term':dictionary[i],'raw_rank':rank,
                'p_word_given_topic':prob[i],'exclusivity':prob[i]/P[:,i].sum(),
                'lift_vs_corpus':prob[i]/background[i],
                'display_rank':chosen_order.get(i,np.nan),
                'normalized_weight_within_display_top10':prob[i]/selected_mass if i in chosen_order else np.nan,
                'display_score':score(i),'display_hidden':dictionary[i] in DISPLAY_STOPWORDS})
    return pd.DataFrame(summaries),pd.DataFrame(terms)


def export_topics(docs,rep,data,families,cfg,out,decision):
    family=families[decision['final_k']]; model=family['model']; P=phi(model); k=P.shape[0]
    ids=[d['id'] for d in docs]; topic_ids=[f'T{i+1:02d}' for i in range(k)]
    unit_theta=model.transform(data['X'])
    theta=aggregate_documents(unit_theta,data['units'],ids,weighted=True)
    equal_chunk=aggregate_documents(unit_theta,data['units'],ids,weighted=False)
    prev=theta.mean(0)
    assert np.allclose(theta.sum(1),1) and np.isclose(prev.sum(),1)
    dt=pd.DataFrame(theta,columns=topic_ids); dt.insert(0,'document_id',ids); dt.insert(1,'filename',[d['filename'] for d in docs])
    table(dt,out/'tables'/'document_topic_matrix.csv')
    entropy=-(theta*np.log(np.maximum(theta,1e-300))).sum(1)
    table([{'document_id':ids[i],'dominant_topic':topic_ids[int(theta[i].argmax())],
        'dominant_topic_weight':float(theta[i].max()),'normalized_topic_entropy':float(entropy[i]/np.log(k)),
        'effective_topic_count':float(np.exp(entropy[i]))} for i in range(len(docs))],out/'tables'/'document_topic_diagnostics.csv')
    ut=pd.DataFrame(unit_theta,columns=topic_ids)
    ut.insert(0,'document_id',[u['document_id'] for u in data['units']]); ut.insert(1,'unit_index',[u['unit_index'] for u in data['units']])
    table(ut,out/'tables'/'unit_topic_matrix.csv')
    summary,keywords=topic_word_tables(model,rep,prev,cfg)
    table(keywords,out/'tables'/'topic_keywords_extended.csv')
    table(keywords[keywords.display_rank.notna()].sort_values(['topic','display_rank']),out/'tables'/'topic_top10_normalized_keywords.csv')
    rows=[]; private_passages=[]; counts=[]
    chosen_train=set(data['training_indices'])
    for d in docs:
        ix=[i for i,u in enumerate(data['units']) if u['document_id']==d['id']]
        counts.append({'document_id':d['id'],'filename':d['filename'],'all_units':len(ix),
            'training_units':sum(i in chosen_train for i in ix),'fewer_than_50_units':len(ix)<50,
            'inference_uses_all_units':True,'in_vocabulary_tokens':int(sum(data['units'][i]['token_count'] for i in ix))})
    table(counts,out/'tables'/'document_chunk_counts.csv')
    for t in range(k):
        for rank,i in enumerate(np.argsort(theta[:,t])[::-1][:3],1):
            doc=docs[i]; ix=[j for j,u in enumerate(data['units']) if u['document_id']==doc['id']]
            best=max(ix,key=lambda j:unit_theta[j,t]); unit=data['units'][best]
            row={'topic':topic_ids[t],'rank':rank,'document_id':doc['id'],'filename':doc['filename'],
                 'document_topic_weight':theta[i,t],'representative_unit':unit['unit_index'],
                 'pdf_page_start':unit['page_start'],'pdf_page_end':unit['page_end']}
            rows.append(row); private_passages.append(dict(**row,normalized_passage=unit['normalized_excerpt']))
    reps=table(rows,out/'tables'/'representative_documents.csv')
    table(private_passages,out/'private'/'representative_passages.csv')
    summary['representative_documents']=[', '.join(reps[reps.topic==tid].document_id) for tid in topic_ids]
    table(summary,out/'tables'/'topic_summary.csv')
    rng=np.random.default_rng(cfg.split_seed)
    boot=np.array([theta[rng.integers(0,len(docs),len(docs))].mean(0) for _ in range(cfg.bootstrap_replicates)])
    seed_prev=[]; matched=[]
    for other in family['models']:
        rr,cc,js,jac=match_topics(P,phi(other))
        other_theta=aggregate_documents(other.transform(data['X']),data['units'],ids)[:,cc]
        seed_prev.append(other_theta.mean(0))
        matched.extend({'reference_topic':topic_ids[a],'other_topic':topic_ids[b],'seed':other.random_state,
                        'js_similarity':s,'top10_jaccard':j} for a,b,s,j in zip(rr,cc,js,jac))
    seed_prev=np.array(seed_prev)
    prevalence=pd.DataFrame({'topic':topic_ids,'mean_document_prevalence':prev,'percent':100*prev,
        'bootstrap_low_conditional':np.quantile(boot,.025,axis=0),
        'bootstrap_high_conditional':np.quantile(boot,.975,axis=0),
        'seed_aligned_mean':seed_prev.mean(0),'seed_aligned_sd':seed_prev.std(0,ddof=1),
        'seed_aligned_min':seed_prev.min(0),'seed_aligned_max':seed_prev.max(0),
        'equal_chunk_within_document_prevalence':equal_chunk.mean(0),
        'naive_all_chunk_prevalence':unit_theta.mean(0),
        'token_weighted_corpus_prevalence':np.average(unit_theta,axis=0,weights=[u['token_count'] for u in data['units']]),
        'dominant_document_count':np.bincount(theta.argmax(1),minlength=k)})
    table(prevalence,out/'tables'/'topic_prevalence.csv'); table(matched,out/'tables'/'seed_topic_alignment.csv')
    table([{'topic':tid,'seed':m.random_state,'mean_document_prevalence':seed_prev[s,t]} for s,m in enumerate(family['models']) for t,tid in enumerate(topic_ids)],out/'tables'/'seed_aligned_prevalence.csv')
    fig,ax=plt.subplots(figsize=(10,5)); order=np.argsort(prev)
    lo=prevalence.bootstrap_low_conditional.to_numpy(); hi=prevalence.bootstrap_high_conditional.to_numpy()
    ax.barh(np.array(topic_ids)[order],prev[order]*100,color='#126782')
    ax.errorbar(prev[order]*100,np.arange(k),xerr=np.array([np.maximum(0,prev-lo),np.maximum(0,hi-prev)])[:,order]*100,fmt='none',ecolor='#202b3c',capsize=3)
    ax.set(xlabel='Mean topic weight across original PDFs (%)',title='Equal-document topic prevalence\n95% bootstrap intervals conditional on the fixed fitted model')
    save_plot(fig,out/'figures','average_topic_prevalence')
    fig,ax=plt.subplots(figsize=(11,5)); image=ax.imshow(theta,aspect='auto',cmap='Blues',vmin=0,vmax=1)
    ax.set(xticks=np.arange(k),xticklabels=topic_ids,xlabel='Topic',ylabel='Original PDF (manifest order)',title='Document-topic proportions')
    fig.colorbar(image,ax=ax,label='Topic weight'); save_plot(fig,out/'figures','document_topic_heatmap')
    fig,ax=plt.subplots(figsize=(8,4)); ax.hist([x['all_units'] for x in counts],bins=min(15,len(docs)),color='#126782',edgecolor='white')
    ax.axvline(50,color='#c95e35',ls='--',label='50-unit training cap; not an eligibility threshold')
    ax.set(xlabel='Units in an original PDF',ylabel='Number of PDFs',title='Chunk-count distribution'); ax.legend(fontsize=8)
    save_plot(fig,out/'figures','chunk_count_distribution')
    # Save complete normalized topic-word matrix, not just a top-term approximation.
    table(pd.DataFrame(P.T,columns=topic_ids).assign(term=[rep['dictionary'][i] for i in range(P.shape[1])]),out/'tables'/'topic_word_probabilities.csv')
    for method in ('cosine','js'):
        S=cosine_similarity(P) if method=='cosine' else 1-cdist(P,P,metric=lambda x,y:float(np.sqrt(max(0,.5*np.sum(x*np.log2(x/((x+y)/2)))+.5*np.sum(y*np.log2(y/((x+y)/2)))))))
        sim=pd.DataFrame(S,columns=topic_ids); sim.insert(0,'topic',topic_ids)
        table(sim,out/'tables'/f'topic_similarity_{method}.csv')
        fig,ax=plt.subplots(figsize=(8,7)); imshow=ax.imshow(S,vmin=0,vmax=1,cmap='Blues')
        ax.set(xticks=np.arange(k),yticks=np.arange(k),xticklabels=topic_ids,yticklabels=topic_ids,title=f'Topic-word similarity: {method.upper()}')
        if k<=15:
            for a in range(k):
                for b in range(k): ax.text(b,a,f'{S[a,b]:.2f}',ha='center',va='center',fontsize=8,color='white' if S[a,b]>.65 else '#222222')
        fig.colorbar(imshow,ax=ax,label='Similarity'); save_plot(fig,out/'figures',f'topic_similarity_{method}')
    quality=[{'metric':'training_variational_lower_bound','value':model.trace_[-1]['variational_bound'],'interpretation':'Approximate evidence lower bound in nats; not exact marginal log likelihood.'},
        {'metric':'training_bound_perplexity','value':model.trace_[-1]['perplexity'],'interpretation':'Training bound-derived perplexity, lower is better on the same data/vocabulary.'},
        {'metric':'overall_c_v','value':model.topic_coherence_['c_v'],'interpretation':'Unweighted mean across raw top-10 topic coherences; window 110.'},
        {'metric':'overall_c_npmi','value':model.topic_coherence_['c_npmi'],'interpretation':'Unweighted mean across raw top-10 topic coherences; window 10.'},
        {'metric':'topic_diversity_top10','value':model.topic_coherence_['topic_diversity'],'interpretation':'Unique terms across all top-10 lists divided by 10K.'},
        {'metric':'outer_iterations','value':model.actual_iterations_,'interpretation':'Actual EM updates observed by the trace hook.'},
        {'metric':'converged','value':int(model.converged_),'interpretation':'Successive training perplexity difference below configured tolerance; no guarantee of global optimum.'},
        {'metric':'articles','value':len(docs),'interpretation':'Independent sampling units remain original documents, not chunks.'}]
    table(quality,out/'tables'/'final_goodness_of_fit.csv')
    try:
        import pyLDAvis
        frequencies=np.asarray(data['X'].sum(0)).ravel(); lengths=np.asarray(data['X'].sum(1)).ravel()
        vis=pyLDAvis.prepare(P,unit_theta,lengths,[rep['dictionary'][i] for i in range(P.shape[1])],frequencies,sort_topics=False,n_jobs=1)
        pyLDAvis.save_html(vis,str(out/'lda_interactive.html'))
        write_json(out/'tables'/'pyldavis_status.json',{'status':'created','topic_numbering':'1 corresponds to T01; sorting disabled',
            'weighting':'pyLDAvis topic areas use token-weighted units; use topic_prevalence.csv for equal-document estimates.'})
    except Exception as e:
        write_json(out/'tables'/'pyldavis_status.json',{'status':'failed','error':str(e)})
        raise RuntimeError(f'pyLDAvis export failed: {e}') from e
    return theta,summary,keywords


def keyword_network(docs,rep,data,cfg,out):
    """One document contributes at most one count to an edge. No overlapping windows."""
    ids=[d['id'] for d in docs]
    Xdoc=sparse.vstack([sparse.csr_matrix(data['X'][[i for i,u in enumerate(data['units']) if u['document_id']==d]].sum(0)) for d in ids],format='csr')
    counts=np.asarray(Xdoc.sum(0)).ravel(); lengths=np.asarray(Xdoc.sum(1)).ravel()
    rel=sparse.diags(1/lengths)@Xdoc
    macro=np.asarray(rel.mean(0)).ravel(); binary=Xdoc.copy(); binary.data[:]=1
    df=np.asarray(binary.sum(0)).ravel(); words=[rep['dictionary'][i] for i in range(Xdoc.shape[1])]
    kws=pd.DataFrame({'term':words,'total_count':counts.astype(int),'document_frequency':df.astype(int),
        'document_percent':100*df/len(docs),'frequency_per_10000_tokens':10000*counts/counts.sum(),
        'mean_document_frequency_per_10000_tokens':10000*macro})
    kws=kws.sort_values(['mean_document_frequency_per_10000_tokens','term'],ascending=[False,True])
    table(kws,out/'tables'/'all_normalized_keywords.csv'); table(kws.head(10),out/'tables'/'top10_normalized_keywords_overall.csv')
    meaningful=kws[~kws.term.isin(DISPLAY_STOPWORDS)]
    table(meaningful.head(10),out/'tables'/'top10_normalized_keywords_display.csv')
    fig,ax=plt.subplots(figsize=(10,5)); top=kws.head(10).iloc[::-1]
    ax.barh(top.term.str.replace('_',' '),top.mean_document_frequency_per_10000_tokens,color='#126782')
    ax.set(xlabel='Mean within-document occurrences per 10,000 retained tokens',title='Top 10 normalized keywords — equal document weighting')
    save_plot(fig,out/'figures','top10_normalized_keywords')
    candidates=meaningful[(meaningful.document_frequency>=cfg.network_min_docs)&
        (meaningful.document_frequency<=cfg.network_max_df*len(docs))].head(cfg.network_terms).term.tolist()
    ix=[rep['dictionary'].token2id[w] for w in candidates]
    co=(binary[:,ix].T@binary[:,ix]).toarray(); freq=df[ix]; edges=[]
    for a,b in itertools.combinations(range(len(ix)),2):
        n=int(co[a,b]); union=freq[a]+freq[b]-n
        jacc=n/union if union else 0
        p=n/len(docs); denom=-np.log(p) if p>0 else np.inf
        npmi=np.log(p/((freq[a]/len(docs))*(freq[b]/len(docs))))/denom if p>0 and denom>0 else 0.0
        if n>=cfg.network_min_docs and jacc>=cfg.network_min_jaccard and npmi>=cfg.network_min_npmi:
            edges.append({'source':candidates[a],'target':candidates[b],'cooccurring_documents':n,
                          'jaccard':float(jacc),'npmi':float(npmi)})
    edges=sorted(edges,key=lambda e:(-e['jaccard'],-e['cooccurring_documents'],e['source'],e['target']))
    table(edges,out/'tables'/'keyword_network_all_eligible_edges.csv',columns=['source','target','cooccurring_documents','jaccard','npmi'])
    shown=edges[:cfg.network_max_edges]; G=nx.Graph()
    for word in candidates:
        i=rep['dictionary'].token2id[word]
        G.add_node(word,document_frequency=int(df[i]),normalized_frequency=float(macro[i]*10000))
    for e in shown: G.add_edge(e['source'],e['target'],weight=e['jaccard'],cooccurring_documents=e['cooccurring_documents'],npmi=e['npmi'])
    communities=list(nx.community.greedy_modularity_communities(G,weight='weight')) if G.number_of_edges() else [{x} for x in G]
    cluster={w:c for c,group in enumerate(communities,1) for w in group}
    nodes=[]
    for node,attrs in G.nodes(data=True):
        attrs['community']=cluster[node]; nodes.append({'term':node,**attrs,'degree':G.degree(node)})
    table(nodes,out/'tables'/'keyword_network_nodes.csv'); table(shown,out/'tables'/'keyword_network_display_edges.csv',columns=['source','target','cooccurring_documents','jaccard','npmi'])
    nx.write_graphml(G,out/'keyword_cooccurrence.graphml')
    # Circular positions avoid collapsed clusters/overlapping labels when a few
    # ubiquitous terms form a dense subgraph. Geometry does not imply distance.
    ordered=sorted(G,key=lambda node:(cluster[node],node))
    fig,ax=plt.subplots(figsize=(14,14)); pos=nx.circular_layout(ordered)
    if G:
        nx.draw_networkx_edges(G,pos,ax=ax,alpha=.22,width=[.5+3*x['weight'] for _,_,x in G.edges(data=True)])
        nx.draw_networkx_nodes(G,pos,ax=ax,node_size=[100+6*G.nodes[x]['document_frequency'] for x in G],node_color=[cluster[x] for x in G],cmap='tab20',alpha=.9)
        for node,(x,y) in pos.items():
            angle=np.degrees(np.arctan2(y,x)); left=x<0
            ax.text(x*1.07,y*1.07,node.replace('_',' '),fontsize=9,
                rotation=angle+(180 if left else 0),rotation_mode='anchor',
                ha='right' if left else 'left',va='center')
    ax.set_title('Keyword co-occurrence across original PDFs\nPositive associations among non-ubiquitous terms; descriptive, not independent LDA validation',pad=25)
    ax.set_xlim(-1.65,1.65); ax.set_ylim(-1.65,1.65); ax.axis('off'); save_plot(fig,out/'figures','keyword_cooccurrence_network')
    write_json(out/'tables'/'keyword_network_definition.json',{'unit':'original PDF; binary term presence',
        'nodes':'top document-normalized terms after display-only filtering and maximum document-frequency filter',
        'edge_weight':'Jaccard = joint document count / union document count',
        'minimum_cooccurring_documents':cfg.network_min_docs,'minimum_jaccard':cfg.network_min_jaccard,
        'minimum_npmi':cfg.network_min_npmi,'maximum_document_frequency_fraction':cfg.network_max_df,
        'plot_edge_cap':cfg.network_max_edges,'eligible_edges':len(edges),'plotted_edges':len(shown),
        'community_method':'greedy modularity on displayed graph; not LDA topic assignments'})
    return Xdoc


def sensitivity_analysis(docs,rep,data,families,cfg,out,decision,theta):
    rows=[]; pending=[]; models=[]; ref=families[decision['final_k']]['model']; P=phi(ref)
    k=decision['final_k']; ids=[d['id'] for d in docs]
    variants=[('whole_document_units',replace(cfg,unit='document'),docs),
        ('chunks_200',replace(cfg,unit='chunk',chunk_size=200,min_tail=50),docs),
        ('chunks_800',replace(cfg,unit='chunk',chunk_size=800,min_tail=100),docs),
        ('uncapped_training_chunks',replace(cfg,max_train_chunks_per_doc=None),docs),
        ('alpha_0_1',replace(cfg,alpha=.1),docs),('eta_0_1',replace(cfg,eta=.1),docs)]
    metadata=None
    if cfg.metadata_csv:
        metadata=pd.read_csv(cfg.metadata_csv).fillna('')
        required={'document_id','publication_type','type_verified'}
        if not required.issubset(metadata): raise ValueError(f'Metadata needs {required}')
        if metadata.document_id.duplicated().any(): raise ValueError('Duplicate document IDs in metadata.')
        merged=pd.DataFrame({'document_id':ids}).merge(metadata,on='document_id',how='left',validate='one_to_one')
        verified=merged.type_verified.astype(str).str.lower().isin(['true','yes','1'])
        known=merged.publication_type.fillna('').astype(str).str.lower().str.strip()
        table(merged.assign(verified_for_analysis=verified),out/'tables'/'publication_type_audit.csv')
        descriptive=pd.DataFrame(theta,columns=[f'T{i+1:02d}' for i in range(k)])
        descriptive['publication_type']=known.where(verified,'unverified')
        table(descriptive.groupby('publication_type').mean().reset_index(),out/'tables'/'prevalence_by_publication_type.csv')
        if verified.all() and not known.isin(['','unknown']).any():
            is_review=known.str.contains(r'review|meta.analysis',regex=True)
            subset=[d for d,keep in zip(docs,~is_review) if keep]
            if len(subset)>=max(12,2*k) and len(subset)<len(docs):
                variants.append(('verified_nonreview_documents',cfg,subset))
            else: pending.append('Review-exclusion refit unavailable: no review group or too few verified non-review documents.')
        else: pending.append('Publication-type sensitivity awaits complete verified classifications; unknown types are never guessed.')
    else: pending.append('Publication-type sensitivity awaits metadata_csv. Complete metadata_template.csv and verify the classifications.')
    if cfg.run_sensitivity:
        for name,variant,subset in variants:
            vd=make_units(subset,rep,variant); X=vd['X'][vd['training_indices']]
            subids=[d['id'] for d in subset]; baseline=theta[[ids.index(i) for i in subids]]
            for seed in cfg.seeds[:3]:
                print(f'Sensitivity: {name} | K={k} | seed={seed}',flush=True)
                model=fit_model(X,k,seed,variant,out/'private'/'cache'/f'sensitivity_{name}_s{seed}.joblib')
                rr,cc,js,jacc=match_topics(P,phi(model))
                other=aggregate_documents(model.transform(vd['X']),vd['units'],subids)[:,cc]
                rows.append({'variant':name,'seed':seed,'documents':len(subset),'training_units':X.shape[0],
                    'iterations':model.actual_iterations_,'converged':model.converged_,
                    'matched_js_to_reference':float(js.mean()),'matched_top10_jaccard':float(jacc.mean()),
                    'document_topic_l1_mean':float(np.abs(other-baseline).sum(1).mean()),
                    'max_prevalence_change_percentage_points':float(np.max(np.abs(other.mean(0)-baseline.mean(0)))*100),
                    'alpha':model.doc_topic_prior_,'eta':model.topic_word_prior_,
                    'comparison':'Same normalized vocabulary; model structure and aligned prevalence on the same subset; no cross-unit ELBO comparison.'})
                models.append(model)
        if models:
            coherence=batch_coherence(models,data['texts'],rep['dictionary'],cfg.coherence_topn)
            for row,coh in zip(rows,coherence): row.update(c_v_full_corpus_reference=coh['c_v'],c_npmi_full_corpus_reference=coh['c_npmi'])
    else: pending.append('Configuration disabled structural sensitivity refits.')
    table(rows,out/'tables'/'sensitivity_runs.csv')
    if rows:
        numeric=pd.DataFrame(rows).select_dtypes(include='number').columns.tolist()
        numeric=[x for x in numeric if x!='seed']
        table(pd.DataFrame(rows).groupby('variant')[numeric].agg(['mean','std']).pipe(lambda x:x.set_axis(['_'.join(c) for c in x.columns],axis=1)).reset_index(),out/'tables'/'sensitivity_summary.csv')
    # Fixed-model influence only; do not call this a leave-one-out refitted model.
    influence=[]
    for i,d in enumerate(docs):
        delta=(theta.sum(0)-theta[i])/(len(docs)-1)-theta.mean(0)
        influence.append({'document_id':d['id'],'filename':d['filename'],
            'max_change_percentage_points':100*float(np.max(np.abs(delta))),
            'definition':'Remove one document from the average with topic model fixed; no refit.'})
    table(influence,out/'tables'/'fixed_model_document_influence.csv')
    write_json(out/'tables'/'sensitivity_status.json',{'completed_variants':sorted(set(r['variant'] for r in rows)),
        'pending':pending,'interpretation':'Sensitivity measures dependence on specifications; it does not prove substantive validity.'})


def human_validation_pack(docs,rep,data,families,cfg,out):
    rng=np.random.default_rng(cfg.split_seed); tasks=[]; keys=[]
    ids=[d['id'] for d in docs]
    for k,fam in families.items():
        model=fam['model']; P=phi(model); ut=model.transform(data['X'])
        dt=aggregate_documents(ut,data['units'],ids)
        summary,keywords=topic_word_tables(model,rep,dt.mean(0),cfg)
        for t in range(k):
            raw=top_terms(model,rep['dictionary'],10)[t]
            intruders=[w for j,terms in enumerate(top_terms(model,rep['dictionary'],30)) if j!=t for w in terms
                       if w not in raw and w not in DISPLAY_STOPWORDS and P[t,rep['dictionary'].token2id[w]]<np.median(P[:,rep['dictionary'].token2id[w]])]
            if not intruders: raise ValueError('Could not construct an unambiguous candidate intruder pool; inspect topic overlap.')
            intruder=intruders[int(rng.integers(len(intruders)))]
            genuine=[w for w in raw if w not in DISPLAY_STOPWORDS][:3]
            if len(genuine)<3: genuine=raw[:3]
            options=genuine+[intruder]; rng.shuffle(options)
            answer='ABCD'[options.index(intruder)]
            doc_ix=np.argsort(dt[:,t])[::-1][:3]
            references=[]; passages=[]
            for di in doc_ix:
                doc=docs[di]; ix=[j for j,u in enumerate(data['units']) if u['document_id']==doc['id']]
                best=max(ix,key=lambda j:ut[j,t]); u=data['units'][best]
                references.append(f'{doc["id"]}: {doc["filename"]}; PDF pp. {u["page_start"]}-{u["page_end"]}')
                passages.append(u['normalized_excerpt'])
            tasks.append({'raw_top10':', '.join(raw),
                'refined_top10':summary.iloc[t].display_top10,
                'representative_sources':' | '.join(references),'normalized_passages':' | '.join(passages),
                **{f'option_{letter}':word for letter,word in zip('ABCD',options)},
                'coherence_rating_1_to_5':'','intruder_choice_A_to_D':'','proposed_label':'','label_evidence_and_page_notes':'',
                'financial_crime_claim_supported_yes_no_unclear':'','rater_name_or_code':''})
            keys.append({'k':k,'topic':f'T{t+1:02d}','model_seed':model.random_state,'intruder_correct_option':answer})
    order=rng.permutation(len(tasks)); blinded=[]; answer_key=[]
    for i,index in enumerate(order,1):
        task_id=f'H{i:03d}'; blinded.append({'task_id':task_id,**tasks[index]}); answer_key.append({'task_id':task_id,**keys[index]})
    directory=out/'private'/'human_validation'
    table(blinded,directory/'rater_1.csv'); table(blinded,directory/'rater_2.csv'); table(answer_key,directory/'answer_key.csv')
    table([{'k':k,'topic':row.topic,'model_seed':fam['model'].random_state,'raw_keywords':row.raw_top10,
        'suggested_keyword_label':row.suggested_label,'final_human_label':'','coder_1_label':'','coder_2_label':'',
        'adjudication_notes':'','supporting_document_ids_and_pdf_pages':'','claim_scope_and_limitations':''}
        for k,fam in families.items()
        for row in topic_word_tables(fam['model'],rep,aggregate_documents(fam['model'].transform(data['X']),data['units'],ids).mean(0),cfg)[0].itertuples()],directory/'topic_label_audit.csv')
    instructions='''# Independent human validation (pending)

Give rater_1.csv and rater_2.csv to two independent coders. Keep answer_key.csv
and suggested model-selection results with the coordinator until coding ends.
Do not show one coder the other's decisions. Tasks are randomized and K/topic IDs
are hidden; keywords can still reveal similarity, so this is partial blinding.

For every row: rate semantic coherence from 1 (incoherent) to 5 (very coherent),
choose the least-fitting item from A-D, propose a concise label, and record PDF
pages supporting that label and any proposed financial-crime claim. The supplied
passages are normalized tokens, NOT verbatim quotations; inspect the actual PDFs.
The algorithmically inserted intruder is a designed task answer, not objective
ground truth about disciplinary meaning. Review ambiguous tasks before coding
and preserve any exclusions with reasons. Do not change a key after seeing ratings.

After independent coding, call analyze_human_ratings(...) in the notebook. It
computes ordinal weighted Cohen kappa, exact agreement, intrusion accuracy and
nominal choice agreement. Small task counts and rater selection limit inference.
Complete topic_label_audit.csv separately, retaining disagreements and adjudication.
Do not report validation as completed just because these blank files were created.
'''
    (directory/'INSTRUCTIONS.md').write_text(instructions,encoding='utf-8')
    write_json(out/'tables'/'human_validation_status.json',{'status':'pending','tasks':len(tasks),
        'required':'Two independent completed rating files and documented label adjudication',
        'ratings_computed':False})


def analyze_human_ratings(rater1_csv,rater2_csv,answer_key_csv,output_dir):
    a=pd.read_csv(rater1_csv).fillna(''); b=pd.read_csv(rater2_csv).fillna(''); key=pd.read_csv(answer_key_csv)
    for d in (a,b,key):
        if d.task_id.duplicated().any(): raise ValueError('Task IDs must be unique.')
    if set(a.task_id)!=set(key.task_id) or set(b.task_id)!=set(key.task_id): raise ValueError('Both raters must have exactly the keyed task IDs.')
    merged=key.merge(a,on='task_id',validate='one_to_one').merge(b,on='task_id',suffixes=('_r1','_r2'),validate='one_to_one')
    c1=pd.to_numeric(merged.coherence_rating_1_to_5_r1,errors='coerce')
    c2=pd.to_numeric(merged.coherence_rating_1_to_5_r2,errors='coerce')
    q1=merged.intruder_choice_A_to_D_r1.astype(str).str.upper().str.strip()
    q2=merged.intruder_choice_A_to_D_r2.astype(str).str.upper().str.strip()
    complete=c1.isin([1,2,3,4,5])&c2.isin([1,2,3,4,5])&q1.isin(list('ABCD'))&q2.isin(list('ABCD'))
    if not complete.all(): raise ValueError(f'{int((~complete).sum())} tasks have missing/invalid ratings. Finish independent coding; missing answers are not imputed.')
    def metrics(mask,name):
        x=c1[mask]; y=c2[mask]; p=q1[mask]; q=q2[mask]; answers=merged.loc[mask,'intruder_correct_option']
        if len(x)<2: raise ValueError('Too few tasks for agreement analysis.')
        return {'scope':name,'tasks':len(x),'coherence_exact_agreement':float((x==y).mean()),
            'coherence_quadratic_weighted_kappa':float(cohen_kappa_score(x,y,labels=[1,2,3,4,5],weights='quadratic')),
            'intrusion_choice_exact_agreement':float((p==q).mean()),
            'intrusion_choice_kappa':float(cohen_kappa_score(p,q,labels=list('ABCD'))),
            'rater1_intrusion_accuracy':float((p==answers).mean()),'rater2_intrusion_accuracy':float((q==answers).mean()),
            'rater1_mean_coherence':float(x.mean()),'rater2_mean_coherence':float(y.mean())}
    results=[metrics(np.ones(len(merged),dtype=bool),'all_tasks')]
    results.extend(metrics(merged.k==k,f'K={k}') for k in sorted(merged.k.unique()))
    out=Path(output_dir); result=table(results,out/'human_agreement_results.csv')
    table(merged,out/'private'/'merged_human_ratings.csv')
    labels_done=all(merged[f'proposed_label_{r}'].astype(str).str.strip().ne('').all() and
                    merged[f'label_evidence_and_page_notes_{r}'].astype(str).str.strip().ne('').all() for r in ('r1','r2'))
    write_json(out/'human_validation_status.json',{'rating_status':'completed','label_evidence_fields_complete':bool(labels_done),
        'adjudication_status':'Requires human review of topic_label_audit.csv',
        'warning':'Kappa can be undefined for constant ratings; a NaN is not evidence of perfect agreement.'})
    return result


REVIEWER_CROSSWALK = [
 ('E7; R1.4g; R1.5c; R1.A8; R1.A17','K choice and random-seed stability','model_selection_summary.csv; seed_stability_cv.csv; full_corpus_seed_stability.csv; seed_topic_alignment.csv','Computed after research run; human interpretability remains pending'),
 ('R1.5b; R1.A17','Convergence and 250 iterations','convergence_traces_cv.csv; convergence_traces_full_corpus.csv; final_convergence_trace.*','Actual outer updates and inner cap distinguished; nonconvergence explicitly reported'),
 ('R1.4c; R1.A4','Exact preprocessing, duplicate, reference and chunk rules','corpus_manifest.csv; extraction_page_audit.csv; normalization_map.csv; unit_manifest.csv; run_config.json','Rules specified; extraction flags and publication identity require review'),
 ('R1.5d; R1.A6','Document-normalized prevalence; fewer than 50 chunks','document_chunk_counts.csv; topic_prevalence.csv; document_topic_matrix.csv; sensitivity_runs.csv','All short documents retained without resampling; all chunks used for inference'),
 ('R1.A7; E7','Author labels and missing Appendix B','topic_summary.csv; representative_documents.csv; private/human_validation/topic_label_audit.csv','Provisional keyword labels only; two-coder support and adjudication pending'),
 ('R1.A9','Co-occurrence graph is descriptive','keyword_network_definition.json; keyword_cooccurrence_network.*; keyword_cooccurrence.graphml','Explicitly not independent confirmation of LDA'),
 ('E5','Mixing primary studies and reviews','metadata_template.csv; prevalence_by_publication_type.csv and verified_nonreview_documents sensitivity when classifications supplied','Author-verified publication types needed; overlapping evidence cannot be inferred from word counts'),
 ('E6; R2.4b','Study quality/risk of bias','metadata_template.csv quality-appraisal fields','Human, design-appropriate study-quality appraisal remains outside LDA'),
 ('E9; R1.A5','Occurrence counts are not evidence strength','all_normalized_keywords.csv; top10_normalized_keywords_overall.csv; topic_prevalence.csv','Explicit denominators; no claim of crime incidence or independent evidence counts'),
 ('E1e; R1.4e; R2.4d; R1.A17','Code/data distinction and package versions','run_config.json; environment_versions.json; requirements-colab.txt; derived_outputs.zip','Copyrighted PDFs and passage text excluded from derived archive; authors verify sharing permissions'),
 ('R1.6b; R1.6c; R1.A13','Readable methods, tables, figures and appendices','METHODS_TEMPLATE.md; topic_summary.csv; figures in PNG/SVG/PDF','Final prose and topic labels require completed research results'),
 ('R1.A10; R2.4e','Small corpus; exploratory interpretation','corpus_flow.json; model-selection notes; sensitivity outputs','Independent N is number of PDFs, not chunks; cannot establish comprehensive coverage'),
 ('E3; E4; R1.3e; R1.4b; R1.4f; R1.A2; R1.A3; R1.A11','Search, access exclusions, screening and PRISMA','Separate screening/eligibility record','Cannot be repaired by running LDA; folder N is not a replacement PRISMA denominator'),
 ('E8; E10; R1.4d; R1.A5; R1.A18; R2.4c','Qwen/Ollama prompts, evidence validation and graph provenance','Separate LLM pipeline and human validation records','This notebook contains no LLM evidence extraction and cannot retrospectively validate that stage'),
]


def write_run_report(docs,cfg,out,decision,families):
    m=families[decision['final_k']]['model']
    table([{'reviewer_item':a,'concern':b,'evidence_outputs':c,'completion_boundary':d} for a,b,c,d in REVIEWER_CROSSWALK],out/'tables'/'reviewer_response_crosswalk.csv')
    text=f'''# Analysis run: {VERSION}

Profile: **{cfg.profile}**. Original included PDFs: **{len(docs)}**.
Provisional diagnostic recommendation: **K={decision['recommended_k']}**.
Final fitted K: **{decision['final_k']}**, medoid seed: **{m.random_state}**.
Actual final-model EM updates: **{m.actual_iterations_}**; numerical stopping criterion met: **{m.converged_}**.

{' '.join(decision['notes'])}

## Interpretation

Training score is an approximate variational evidence lower bound, not an exact
marginal likelihood. Predictive log likelihood is a plug-in document-completion
score: topic proportions are inferred from one random token half and the other
half is scored. It is not an unbiased marginal-likelihood estimator. Vocabulary
and learned phrases are fitted within each training fold. Validation splits keep
each PDF and flagged near-duplicate family together. The folds guide model
selection; these are not an untouched final test set or population estimates.

Chunking is performed within each PDF after normalization, with size {cfg.chunk_size},
zero overlap and tails under {cfg.min_tail} tokens merged into the previous chunk.
At most {cfg.max_train_chunks_per_doc} evenly spaced chunks per PDF train the model,
without replacement. Every available chunk is used to infer its PDF's topic
distribution. Documents with fewer than 50 chunks contribute all their chunks;
none is duplicated or excluded for that reason. Longer PDFs can still exert more
influence on fitting. Unit and cap sensitivity checks evaluate this dependence.

For PDF d, theta_dk = sum_c(n_dc * theta_dck) / sum_c(n_dc), where n_dc counts
retained vocabulary tokens in nonoverlapping chunk c. Overall prevalence is
(1/D) * sum_d(theta_dk). Each PDF has equal weight in that final average. This
maps thematic attention in the included literature, not financial-crime
incidence, methodological quality or the strength of independent evidence.

Bootstrap intervals resample original PDFs with the fitted model held fixed.
They describe conditional dispersion only, excluding model-selection, seed,
extraction and search-coverage uncertainty. Seed dispersion is reported separately.
Network edges represent document-level co-presence. They cannot independently
validate LDA, establish causality, or validate author-derived substantive labels.

## Reviewer response status

See tables/reviewer_response_crosswalk.csv and the [live reviewer document]({REVIEW_URL}).
Blank coding templates are not completed human validation. Publication-type
sensitivity needs verified metadata. Study-quality appraisal, screening reliability,
PRISMA reconciliation and Qwen validation remain separate author tasks.

## Navigation

- tables/model_selection_summary.csv: cross-validation and multi-seed comparison.
- model_selection_decision.json: transparent decision rule and qualifications.
- tables/final_goodness_of_fit.csv: final fit, coherence and convergence.
- tables/topic_summary.csv: concise provisional topic table.
- tables/topic_prevalence.csv: equal-document estimates and weighting alternatives.
- lda_interactive.html: interactive pyLDAvis (token-weighted areas; topic IDs preserved).
- figures/: all figures in 300-dpi PNG plus vector SVG/PDF.
- private/: cached models, text, excerpts and human-validation worksheets.
- derived_outputs.zip: tables, figures and run reports; excludes private content/PDFs.

## Sources for the implementation

- [LDA and variational inference](https://jmlr.org/papers/v3/blei03a.html)
- [scikit-learn LDA API](https://scikit-learn.org/1.7/modules/generated/sklearn.decomposition.LatentDirichletAllocation.html)
- [Gensim coherence pipeline](https://radimrehurek.com/gensim/models/coherencemodel.html)
- [Wallach and colleagues on evaluating topic models](https://homepages.inf.ed.ac.uk/imurray2/pub/09etm/)
- [Röder and colleagues on topic coherence](https://doi.org/10.1145/2684822.2685324)
'''
    (out/'RUN_REPORT.md').write_text(text,encoding='utf-8')
    method=f'''# Methods text to adapt after validation

**Draft with computational facts only; add final human labels and author decisions.**

We conducted an exploratory LDA analysis of {len(docs)} full-text documents.
PDF text was extracted locally using PyMuPDF, with a pypdf fallback and logged
page-level diagnostics. Delivery covers and a hash-verified chapter-front-matter
range were excluded. Reference sections were removed only at standalone
reference headings after {cfg.reference_min_fraction:.0%} of cleaned text. Exact
file/content duplicates were logged; near-duplicate candidates were retained and
placed within the same validation fold. Text normalization included Unicode
repair, an explicit domain-alias dictionary, noun lemmatization and auditable
adjacent-repeat removal. Learned phrase detection and vocabulary filters were
fitted on training documents within each validation fold.

We compared K={list(cfg.k_values)} with seeds {list(cfg.seeds)} using
{cfg.folds} document-grouped folds. LDA used batch variational inference,
alpha={cfg.alpha if cfg.alpha is not None else '1/K'} and eta={cfg.eta}, a maximum
of {cfg.max_iter} outer EM updates and {cfg.max_doc_update_iter} inner updates.
We logged the variational bound at every outer update. Training perplexity,
document-completion log scores, C_v (110-token window), C_NPMI (10-token window),
top-{cfg.coherence_topn} diversity, and Hungarian-matched seed stability informed
model selection. Complete results and the declared selection rule accompany
this script. Fold dispersion is descriptive; the validation folds were used for
selection and are not an independent post-selection test set.

The computational rule recommended K={decision['recommended_k']}; the final
fit used K={decision['final_k']} and the medoid seed {m.random_state}.
**Before reporting this as the preferred solution, resolve diagnostic flags,
complete independent interpretability assessments, and state any override.**
Topic labels are author interpretations that require supporting document/page
references. Prevalence averages token-weighted chunk proportions within each
document, then weights documents equally. The keyword network describes
document-level lexical co-occurrence and is not an independent model-validation
test. Results describe this corpus's thematic structure; they do not estimate
crime prevalence, validate proposed safeguards, or substitute for study appraisal.

**Complete separately:** screening/search/PRISMA account; study-type/quality
appraisal; coder identities and blinding; agreement results and disagreements;
final K justification; label adjudication; limitations; data-sharing declaration.
'''
    (out/'METHODS_TEMPLATE.md').write_text(method,encoding='utf-8')


def validate_outputs(out,docs,data,theta,decision):
    checks={}
    checks['all_document_rows_present']=theta.shape[0]==len(docs)
    checks['document_probabilities_sum_to_one']=bool(np.allclose(theta.sum(1),1))
    checks['mean_prevalence_sums_to_one']=bool(np.isclose(theta.mean(0).sum(),1))
    checks['nonnegative_counts']=bool((data['X'].data>=0).all())
    checks['training_units_no_replacement']=len(data['training_indices'])==len(set(data['training_indices']))
    s=pd.read_csv(out/'tables'/'document_validation_splits.csv')
    checks['validation_has_no_group_leakage']=all(not set(g[g.part=='train'].group)&set(g[g.part=='validation'].group) for _,g in s.groupby('fold'))
    checks['every_document_validated_once']=bool((s[s.part=='validation'].document_id.value_counts()==1).all())
    p=pd.read_csv(out/'tables'/'topic_word_probabilities.csv')
    checks['topic_word_probabilities_sum_to_one']=bool(np.allclose(p.drop(columns='term').sum(),1))
    top=pd.read_csv(out/'tables'/'topic_top10_normalized_keywords.csv')
    checks['display_keyword_weights_sum_to_one']=bool(np.allclose(top.groupby('topic').normalized_weight_within_display_top10.sum(),1))
    for method in ('cosine','js'):
        sim=pd.read_csv(out/'tables'/f'topic_similarity_{method}.csv').drop(columns='topic').to_numpy()
        checks[f'{method}_similarity_symmetric']=bool(np.allclose(sim,sim.T))
    required=['topic_summary.csv','final_goodness_of_fit.csv','top10_normalized_keywords_overall.csv',
        'topic_prevalence.csv','model_selection_summary.csv','convergence_traces_full_corpus.csv',
        'keyword_network_display_edges.csv','reviewer_response_crosswalk.csv']
    checks['requested_tables_exist']=all((out/'tables'/p).exists() for p in required)
    checks['interactive_lda_created']=(out/'lda_interactive.html').exists()
    write_json(out/'verification.json',{'checks':checks,'all_pass':all(checks.values()),
        'validation_scope':'Software consistency, not substantive topic validity','profile':decision.get('profile','see run_config.json')})
    if not all(checks.values()): raise AssertionError(f'Output integrity check failed: {checks}')
    return checks


def package_outputs(out):
    out=Path(out); manifest=[]
    files=[p for p in out.rglob('*') if p.is_file() and 'private' not in p.relative_to(out).parts and p.suffix.lower()!='.zip' and p.name!='output_checksums.csv']
    for p in sorted(files):
        manifest.append({'file':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    table(manifest,out/'output_checksums.csv'); files.append(out/'output_checksums.csv')
    with zipfile.ZipFile(out/'derived_outputs.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in files: z.write(p,p.relative_to(out).as_posix())


def run_pipeline(config=None):
    cfg=(config or Config()).checked()
    source=Path(cfg.input_dir).expanduser().resolve()
    pdfs=sorted(p for p in source.rglob('*') if p.is_file() and p.suffix.lower()=='.pdf')
    if not pdfs: raise FileNotFoundError(f'No PDFs found at {source}')
    fingerprints=[(p.relative_to(source).as_posix(),hashlib.sha256(p.read_bytes()).hexdigest()) for p in pdfs]
    versions={p:im.version(p) for p in PACKAGES}
    code_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest() if '__file__' in globals() else globals().get('NOTEBOOK_CODE_SHA256',VERSION)
    key=digest({'config':asdict(cfg),'pdfs':fingerprints,'versions':versions,'code':code_hash,
        'aliases':DOMAIN_ALIASES,'page_rules':load_page_rules(cfg),
        'metadata_sha':hashlib.sha256(Path(cfg.metadata_csv).read_bytes()).hexdigest() if cfg.metadata_csv else ''})
    out=Path(cfg.output_dir).expanduser().resolve()/('run_'+key[:12])
    for name in ('tables','figures','private'): (out/name).mkdir(parents=True,exist_ok=True)
    public_config=asdict(cfg)
    for field in ('input_dir','output_dir'): public_config[field]='USER_SUPPLIED_DIRECTORY'
    for field in ('metadata_csv','page_rules_csv'): public_config[field]=Path(public_config[field]).name if public_config[field] else ''
    write_json(out/'run_config.json',public_config)
    write_json(out/'private'/'runtime_config.json',asdict(cfg))
    write_json(out/'tables'/'preprocessing_definitions.json',{'domain_aliases':DOMAIN_ALIASES,
        'model_stopwords':sorted(set(ENGLISH_STOP_WORDS)|MODEL_BOILERPLATE|set(cfg.extra_stopwords)),
        'display_stopwords':sorted(DISPLAY_STOPWORDS),
        'note':'Display filtering does not alter model fitting or raw-term coherence. Paragraph block extraction is approximate; inspect source-page references.'})
    write_json(out/'environment_versions.json',{'python':sys.version,'platform':platform.platform(),'packages':versions,'pipeline_version':VERSION,'code_sha256':code_hash,'run_hash':key})
    if '__file__' in globals():
        (out/'analysis_source.py').write_text(Path(__file__).read_text(encoding='utf-8'),encoding='utf-8')
    resolved=sorted({f'{d.metadata["Name"]}=={d.version}' for d in im.distributions() if d.metadata.get('Name')})
    (out/'requirements-resolved.txt').write_text('\n'.join(resolved)+'\n',encoding='utf-8')
    print(f'Outputs/checkpoints: {out}',flush=True)
    setup_resources(out,cfg)
    docs,manifest=audit_corpus(cfg,out)
    summary,runs=cross_validate(docs,cfg,out)
    decision=recommend_k(summary,cfg,out)
    print(f'Diagnostic K={decision["recommended_k"]}; final K={decision["final_k"]}. Check all qualifications.',flush=True)
    rep,data,families=fit_final_candidates(docs,cfg,out,decision)
    theta,topics,keywords=export_topics(docs,rep,data,families,cfg,out,decision)
    keyword_network(docs,rep,data,cfg,out)
    sensitivity_analysis(docs,rep,data,families,cfg,out,decision,theta)
    human_validation_pack(docs,rep,data,families,cfg,out)
    write_run_report(docs,cfg,out,decision,families)
    validate_outputs(out,docs,data,theta,decision)
    package_outputs(out)
    print(f'COMPLETE: {out}\nHuman labels/validation remain pending. Profile: {cfg.profile}',flush=True)
    return {'output_dir':out,'decision':decision,'topic_summary':topics,'model_selection':summary,'documents':len(docs)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir',required=True)
    parser.add_argument('--output-dir',default='lda_results')
    parser.add_argument('--profile',choices=['research','smoke'],default='research')
    parser.add_argument('--metadata-csv',default='')
    parser.add_argument('--page-rules-csv',default='')
    parser.add_argument('--config-json',help='Optional JSON with other Config fields; CLI paths/profile take precedence')
    args=parser.parse_args(); settings=json.loads(Path(args.config_json).read_text(encoding='utf-8')) if args.config_json else {}
    settings.update(input_dir=args.input_dir,output_dir=args.output_dir,profile=args.profile,
                    metadata_csv=args.metadata_csv,page_rules_csv=args.page_rules_csv)
    run_pipeline(Config(**settings))


if __name__=='__main__':
    main()
