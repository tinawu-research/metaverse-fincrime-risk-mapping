"""Compare saved K=11 alternatives with same-seed baselines; never fit a model."""
from pathlib import Path
import argparse,csv,json
import numpy as np
import joblib
from scipy.spatial.distance import jensenshannon
from scipy.optimize import linear_sum_assignment
import Metaverse_LDA_Colab  # exposes the recorded TracedLDA class for saved models

def topic_words(path):
    model=joblib.load(path)
    return model.components_/model.components_.sum(axis=1,keepdims=True)

def compare(run_dir,output_dir):
    run_dir=Path(run_dir).resolve();out=Path(output_dir).resolve();out.mkdir(parents=True,exist_ok=True)
    seeds=[11,42,97]
    variants=['whole_document_units','chunks_200','chunks_800','uncapped_training_chunks','alpha_0_1','eta_0_1']
    baseline={s:topic_words(run_dir/f'private/cache/full_k11_s{s}.joblib') for s in seeds}
    pairs=[]
    for variant in variants:
        for seed in seeds:
            ref=baseline[seed];alt=topic_words(run_dir/f'private/cache/sensitivity_{variant}_s{seed}.joblib')
            if ref.shape!=alt.shape:raise ValueError('Vocabulary/topic dimensions differ')
            distance=np.array([[jensenshannon(a,b,base=2) for b in alt] for a in ref])
            ri,ai=linear_sum_assignment(distance)
            jac=[]
            for a,b in zip(ri,ai):
                ra=set(np.argsort(ref[a])[-10:]);rb=set(np.argsort(alt[b])[-10:])
                jac.append(len(ra&rb)/len(ra|rb))
            pairs.append({'variant':variant,'seed':seed,'matched_js_similarity':float(np.mean(1-distance[ri,ai])),
                          'matched_top10_jaccard':float(np.mean(jac)),
                          'max_abs_topic_word_difference_after_matching':float(np.max(np.abs(ref[ri]-alt[ai])))})
    summaries=[]
    for v in variants:
        rows=[r for r in pairs if r['variant']==v]
        summaries.append({'variant':v,'n':len(rows),'mean_js_similarity':float(np.mean([x['matched_js_similarity'] for x in rows])),
                          'min_js_similarity':min(x['matched_js_similarity'] for x in rows),
                          'max_js_similarity':max(x['matched_js_similarity'] for x in rows),
                          'mean_top10_jaccard':float(np.mean([x['matched_top10_jaccard'] for x in rows])),
                          'max_abs_difference':max(x['max_abs_topic_word_difference_after_matching'] for x in rows)})
    for name,rows in [('paired_sensitivity_pairs.csv',pairs),('paired_sensitivity_summary.csv',summaries)]:
        with (out/name).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (out/'paired_sensitivity_audit.json').write_text(json.dumps({'pairs':pairs,'summary':summaries},indent=2),encoding='utf-8')
    print(json.dumps(summaries,indent=2))
    return pairs,summaries

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',required=True,help='Completed run containing trusted private/cache model files')
    p.add_argument('--output-dir',required=True,help='Separate destination for the audit tables')
    a=p.parse_args();compare(a.run_dir,a.output_dir)
