"""Small synthetic P1–P5 execution: no real Test records are opened."""
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import yaml
from src.io import write_json, sha256, read_json
from src.experiment import Experiment


def fixture_project(tmp_path):
    root=Path(__file__).resolve().parents[1]
    shutil.copytree(root/'src',tmp_path/'src'); shutil.copytree(root/'configs',tmp_path/'configs')
    raw=tmp_path/'data/raw'; raw.mkdir(parents=True)
    rng=np.random.default_rng(7); manifest={'datasets':{}}; config={}
    for name in ['dry_bean','rice','bank_marketing']:
        X=pd.DataFrame(rng.normal(size=(200,3)),columns=['a','b','c']); X['Class']=np.where(X.a>0,'one','zero')
        path=raw/f'{name}.csv'
        if name=='bank_marketing':
            X['duration']=1.; X['pdays']=999; path=raw/'bank-additional-full.csv'
        X.to_csv(path,index=False,sep=';' if name=='bank_marketing' else ',')
        manifest['datasets'][name]={'raw_file':path.name,'sha256':sha256(path)}
        config[name]={'rows':200,'features':len(X.columns)-1,'labels':['zero','one'],'temporal':name=='bank_marketing'}
    write_json(raw/'dataset_manifest.json',manifest)
    (tmp_path/'configs/datasets.yaml').write_text(yaml.safe_dump(config))
    exp=yaml.safe_load((tmp_path/'configs/experiments.yaml').read_text()); exp.update(seeds=[42],grid=[0,.5],bootstrap_replicates=3)
    (tmp_path/'configs/experiments.yaml').write_text(yaml.safe_dump(exp))
    models=yaml.safe_load((tmp_path/'configs/models.yaml').read_text()); models['mlp']['epochs']=2; models['rf']['n_estimators']=5
    (tmp_path/'configs/models.yaml').write_text(yaml.safe_dump(models))
    return tmp_path


def test_end_to_end_and_freeze_tamper(tmp_path):
    exp=Experiment(fixture_project(tmp_path),'FULL')
    for s in ['P1','P2','P3','P4']: exp.run(s)
    assert not (exp.out/'test_access.json').exists()
    exp.run('P5')
    assert all(v=='PASS' for v in exp.state.values())
    for f in ['summary.csv','statistical_summary.csv','ablation_results.csv']: assert (exp.out/f).stat().st_size>0
    frozen=read_json(exp.out/'frozen_protocol.json')
    artifact=tmp_path/next(iter(frozen['artifact_hashes']))
    artifact.write_bytes(b'tampered')
    with pytest.raises(RuntimeError,match='integrity'): exp.verify_freeze()


@pytest.mark.parametrize('mode', ['SMOKE', 'PILOT'])
def test_development_modes_never_open_test(tmp_path,monkeypatch,mode):
    import src.experiment as module
    exp=Experiment(fixture_project(tmp_path),mode)
    original=module.load_split
    def guard(path,split,**kwargs):
        assert split!='test'
        return original(path,split,**kwargs)
    monkeypatch.setattr(module,'load_split',guard)
    for s in ['P1','P2','P3','P4','P5']: exp.run(s)
    assert exp.state['P5']=='NOT_RUN'
    assert not (exp.out/'test_access.json').exists()
