"""Read-only audit; never constructs Experiment or fits/predicts a model."""
import sys, json, hashlib, itertools
from pathlib import Path
import pandas as pd
import numpy as np
import joblib, yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data import readiness, prepare_features
from src.io import sha256, digest, versions
ID='full-62500e11e892b899'
def audit(output):
    out=ROOT/'results'/ID
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    frozen=read(out/'frozen_protocol.json'); sig=read(out/'experiment.json')
    checks={}
    checks['freeze_checksum']=sha256(out/'frozen_protocol.json')==read(out/'frozen_protocol.sha256.json')['sha256']
    checks['experiment_id']='full-'+digest(sig)[:16]==ID
    checks['signature']=sig==frozen['signature']
    checks['source_hashes']=all(sha256(ROOT/p)==h for p,h in sig['code'].items())
    checks['config']=all(yaml.safe_load((ROOT/f'configs/{n}.yaml').read_text())==v for n,v in sig['config'].items())
    checks['raw_manifest']=sha256(ROOT/'data/raw/dataset_manifest.json')==sig['raw_manifest']
    hashes=[]
    for i,(p,h) in enumerate(frozen['artifact_hashes'].items()):
        actual=sha256(ROOT/p) if (ROOT/p).is_file() else None
        hashes.append({'path':p,'expected':h,'actual':actual,'pass':actual==h})
        if i%100==0: print('Frozen artifacts:',i,flush=True)
    checks['frozen_artifacts']=all(x['pass'] for x in hashes)
    frames,raw=readiness(ROOT,sig['config']['datasets'])
    labels=[]; splits=[]
    for p in (ROOT/'data/splits'/ID).rglob('*.json'):
        ds=p.parent.name; data=read(p); X,y=frames[ds]
        groups=pd.util.hash_pandas_object(prepare_features(X,ds),index=False).to_numpy()
        ids=data['indices']; allids=[i for v in ids.values() for i in v]
        good=len(allids)==len(set(allids)) and len(allids)+len(data['purged'])==len(X)
        good=good and all(not set(groups[ids[a]])&set(groups[ids[b]]) for a,b in itertools.combinations(ids,2))
        splits.append({'dataset':ds,'manifest':p.name,'pass':good})
        for split,ix in ids.items():
            counts=y.iloc[ix].value_counts().to_dict()
            labels.append({'dataset':ds,'seed':p.stem,'split':split,'rows':len(ix),'counts':counts,'yes_rate':float((y.iloc[ix]=='yes').mean()) if ds=='bank_marketing' else None})
    checks['split_disjointness']=all(x['pass'] for x in splits)
    frame=pd.read_csv(out/'per_seed_results.csv'); one=frame[(frame.B==8)&(frame.target_coverage==.9)]
    keys=['dataset','model','seed','condition','level']
    expected=set(itertools.product(sig['datasets'],['lr','rf','mlp'],[13,21,42,87,101],[('clean',0.),('missing',.05),('missing',.1),('missing',.2),('gaussian',.01),('gaussian',.05),('gaussian',.1),('quantization',.02),('quantization',.05),('quantization',.1)]))
    actual={(r.dataset,r.model,r.seed,(r.condition,r.level)) for r in one.itertuples()}
    checks['450_primary_cells']=actual==expected
    checks['unique_rows']=not frame.duplicated(keys+['B','scorer','target_coverage']).any()
    checks['B_ablations']=set(frame.B)=={4,8,16}
    checks['all_status_pass']=all(v=='PASS' for v in read(out/'status.json').values())
    checks['development_no_C3']=all(c[0]!='quantization' for c in frozen['development_conditions'])
    # Read saved predictions and receipts only: no Test inference or recomputation of scientific metrics.
    cached=[]; receipts=[]; cache_metric_checks=[]
    indexed=frame.set_index(keys+['B','scorer','target_coverage'])['aurc'].to_dict()
    for i,p in enumerate(sorted((out/'predictions').glob('*_B8_*.joblib'))):
        receipt=read(p.with_suffix('.json')); good=sha256(p)==receipt['sha256']
        receipts.append({'file':p.name,'sha256':receipt['sha256'],'pass':good})
        if not good: continue
        r=joblib.load(p); m=r['metrics'][0]; c=r['classification']; f=r['features']
        for metric in r['metrics']:
            key=tuple(metric[k] for k in keys+['B','scorer','target_coverage'])
            cache_metric_checks.append(key in indexed and np.isclose(indexed[key],metric['aurc'],rtol=1e-12,atol=1e-14))
        pred=np.asarray(f['p']).argmax(1); cm=np.asarray(c['confusion_matrix'])
        cached.append({**{k:m[k] for k in ['dataset','model','seed','condition','level']},'accuracy':c['accuracy'],'macro_f1':c['macro_f1'],'confusion_matrix':cm.tolist(),'predicted_counts':np.bincount(pred,minlength=cm.shape[0]).tolist(),'cache':p.name,'sha256':receipt['sha256']})
        if i%100==0:print('Read saved primary predictions:',i,flush=True)
    checks['450_prediction_receipts']=len(receipts)==450 and all(x['pass'] for x in receipts)
    # Cross-check every saved primary metric against corresponding CSV, without recomputing it.
    checks['primary_csv_matches_cache']=all(cache_metric_checks)
    result={'experiment':ID,'checks':checks,'frozen_artifacts':hashes,'raw':raw,'splits':splits,'labels':labels,'classification':cached,'prediction_receipts':receipts,'versions_current':versions(),'versions_frozen':sig['versions'],'status':read(out/'status.json'),'selected_cpcr_B8':[r for r in frozen['selections'] if r['B']==8 and r['scorer']=='cpcr']}
    Path(output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(checks,indent=2),flush=True)
if __name__=='__main__':audit(sys.argv[1])
