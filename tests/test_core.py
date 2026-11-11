from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from src.metrics import ranking, curve, classification, deployment, probabilities
from src.data import split_indices, load_split
from src.preprocessing import make_preprocessor
from src.corruptions import Corruptor, instability, geometry_violations
from src.cpcr import ConditionalECDF, cpcr
from src.calibration import calibrate, select
from src.risk_baselines import SCORERS, score
from src.io import save, read_json, write_json, sha256


def test_known_risk_values():
    r = ranking([0, 1], [0, 1])
    assert r['aurc'] == .25 and r['augrc'] == .25 and r['failure_auroc'] == 1
    assert ranking([0,1],[1,0])['aurc'] == .75
    assert ranking([0,0],[0,1])['failure_auroc'] is None
    assert ranking([0,1],[1,1])['aurc'] == .5
    assert ranking([1,0],[1,1])['aurc'] == .5


def test_classification_known():
    r = classification(np.array([0,1]), np.array([[1.,0],[0,1.]]))
    assert r['accuracy'] == 1 and r['brier'] == 0 and r['ece'] == 0
    with pytest.raises(ValueError): probabilities([[.2,.2]])


def test_threshold_ties_and_empty_acceptance():
    assert calibrate([1,1,1,2],[.8])['0.8'] == 2
    assert deployment([0,1],[1,2],0)['realized_selective_risk'] is None
    assert deployment([0,1],[1,2],1)['realized_coverage'] == .5
    with pytest.raises(PermissionError): calibrate([1],[.8],split='test')


def test_ecdf_and_direction():
    ref = ConditionalECDF(2,1).fit([.1,.2,.8,.9],[0,.2,.6,.8])
    np.testing.assert_allclose(ref.transform([.1,.8],[.1,.7]),[.5,.5])
    fallback = ConditionalECDF(10,20).fit([0,1],[0,1])
    assert fallback.transform([.2],[.5])[0] == .5
    assert np.all(np.diff(cpcr(np.arange(10)/10,np.arange(10)/10,.5,.5)) >= 0)
    with pytest.raises(PermissionError): ref.fit([1],[1],split='test')


def test_corruptions_preserve_input_and_categories():
    X = pd.DataFrame({'Area': [10.,20.,30.], 'Extent':[.2,.5,.8], 'kind':['a','b','unknown']})
    original = X.copy(deep=True); c = Corruptor().fit(X)
    for kind, level in [('missing',.2),('gaussian',.1),('quantization',.1)]:
        a = c.transform(X,kind,level,42); b = c.transform(X,kind,level,42)
        pd.testing.assert_frame_equal(a,b); pd.testing.assert_frame_equal(X,original)
        if kind != 'missing': assert a.kind.equals(X.kind)
    assert c.transform(X,'missing',1,42).isna().all().all()
    assert geometry_violations(c.transform(X,'gaussian',10,42))['Area_nonpositive'] == 0


def test_instability_zero_and_max():
    X = pd.DataFrame({'a': [0.,1.,2.]}); c = Corruptor().fit(X)
    class Constant:
        def predict_proba(self, X): return np.tile([1.,0.],(len(X),1))
    assert np.all(instability(Constant(),X,c) == 0)
    assert np.allclose(instability(Constant(),X,c,base=np.tile([0.,1.],(3,1))),1)


def test_group_splits_and_temporal():
    X = pd.DataFrame({'x': np.repeat(np.arange(200),2)}); y = np.repeat(np.arange(200)%2,2)
    a,purge = split_indices(X,y,42); b,_ = split_indices(X,y,42)
    for key in a: np.testing.assert_array_equal(a[key],b[key])
    for i,key in enumerate(a):
        for other in list(a)[i+1:]: assert not set(X.iloc[a[key]].x) & set(X.iloc[a[other]].x)
    t,_ = split_indices(X,y,13,True); t2,_ = split_indices(X,y,87,True)
    for key in t: np.testing.assert_array_equal(t[key],t2[key])
    assert max(t['train']) < min(t['model_val'])


def test_train_only_preprocessor():
    X = pd.DataFrame({'a':[1.,3.,np.nan], 'c':['a','a','b']})
    prep = make_preprocessor(X).fit(X)
    assert prep.named_transformers_['numeric'].named_steps['imputer'].statistics_[0] == 2
    assert np.isfinite(prep.transform(pd.DataFrame({'a':[10000.,np.nan],'c':['unseen','a']}))).all()
    assert prep.named_transformers_['numeric'].named_steps['imputer'].statistics_[0] == 2


def test_all_risk_scores_and_selection_guard():
    p = np.array([[.8,.2],[.4,.6]]); v=np.array([.1,.2]); q=np.array([.2,.4])
    for scorer in SCORERS: assert np.isfinite(score(scorer,p,v,q,.5,.5)).all()
    dev = [{'p':p,'v':v,'q':q,'errors':np.array([0,1]),'split':'risk_val','kind':'clean'}]
    chosen, _ = select('cpcr',dev,[0,.5]); assert chosen['lambda'] == 0
    dev[0]['kind']='quantization'
    with pytest.raises(PermissionError): select('cpcr',dev,[0])
    with pytest.raises(PermissionError): load_split(Path('nonexistent'),'test')


def test_atomic_serialization(tmp_path):
    path=tmp_path/'nested/a.json'; write_json(path,{'a':np.array([1,2])})
    assert read_json(path)=={'a':[1,2]}; assert len(sha256(path))==64


def test_cluster_bootstrap_identical_scores():
    from src.evaluation import paired_cluster_bootstrap
    r={'features':{'row_id':np.arange(5),'errors':np.array([0,1,0,1,0])},
       'scores':{'msp':np.arange(5),'cpcr':np.arange(5)}}
    assert paired_cluster_bootstrap([r,r],'cpcr',10)==[0,0]


@pytest.mark.parametrize('kind',['lr','rf','mlp'])
def test_models_reload(tmp_path,kind):
    import joblib
    from src.models import train
    rng=np.random.default_rng(42); X=pd.DataFrame(rng.normal(size=(80,3)),columns=list('abc')); y=(X.a>0).astype(int).to_numpy()
    prep=make_preprocessor(X.iloc[:60],kind!='rf').fit(X.iloc[:60])
    cfg={'lr':{'C':1.,'max_iter':2000},'rf':{'n_estimators':5,'min_samples_leaf':2,'n_jobs':1},
         'mlp':{'hidden':[64,32],'learning_rate':.001,'batch_size':16,'epochs':2,'patience':2}}[kind]
    model,_=train(kind,prep,X.iloc[:60],y[:60],X.iloc[60:],y[60:],cfg,42,tmp_path)
    p=probabilities(model.predict_proba(X.iloc[60:])); save(tmp_path/'model.joblib',model)
    np.testing.assert_allclose(p,joblib.load(tmp_path/'model.joblib').predict_proba(X.iloc[60:]))


def test_temporal_conflicting_labels_do_not_drive_purge():
    X=pd.DataFrame({'x':np.arange(100,dtype=float)})
    X.loc[60,'x']=0
    y=np.arange(100)%2; y[60]=1
    splits,purged=split_indices(X,y,13,True)
    assert purged==[60] and 0 in splits['train']
    y[60]=0
    again,purged_again=split_indices(X,y,87,True)
    assert purged_again==purged
    for key in splits: np.testing.assert_array_equal(splits[key],again[key])


def test_float32_probability_roundoff():
    p=np.array([[.3,.7],[.1,.9]],dtype=np.float32)
    normalized=probabilities(p)
    np.testing.assert_allclose(normalized.sum(1),1,atol=1e-15)
    assert np.isfinite(classification(np.array([0,1]),p)['nll'])
