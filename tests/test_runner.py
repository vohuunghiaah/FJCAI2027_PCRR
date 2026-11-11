import json
from types import SimpleNamespace
from run_all import prerequisite_message


def test_environment_drift_diagnostic(tmp_path):
    old = tmp_path/'results/pilot-old'
    old.mkdir(parents=True)
    (old/'experiment.json').write_text(json.dumps({'versions': {'python': '3.13.16'}, 'code': {'a': 'hash'}}))
    (old/'status.json').write_text(json.dumps({'P3': 'PASS'}))
    exp = SimpleNamespace(root=tmp_path, out=tmp_path/'results/pilot-new', mode='PILOT',
        id='pilot-new', datasets=['dry_bean','rice'],
        signature={'versions': {'python': '3.13.18'}, 'code': {'a': 'hash'}})
    message = prerequisite_message(exp, 'P4')
    assert 'python: 3.13.16 -> 3.13.18' in message
    assert 'pilot-old' in message
    assert '--mode PILOT --stage all' in message
    assert 'code changed' not in message


def test_missing_previous_run_diagnostic(tmp_path):
    exp=SimpleNamespace(root=tmp_path,out=tmp_path/'results/full-new',mode='FULL',
        id='full-new',datasets=['dry_bean','rice','bank_marketing'],signature={})
    message=prerequisite_message(exp,'P4')
    assert '--bank --stage all' in message
    assert 'FULL all includes P5' in message


def test_stage_all_retains_passed_stages_and_one_experiment(monkeypatch,tmp_path):
    import sys
    import run_all
    import src.experiment
    created=[]; called=[]
    class Existing:
        def __init__(self,*args):
            self.id='pilot-fixed'; self.out=tmp_path
            self.state={f'P{i}':'PASS' for i in range(1,5)} | {'P5':'NOT_RUN'}
            created.append(self)
        def run(self,stage):
            called.append((self.id,stage))
            assert stage=='P5', 'Completed P1-P4 must not rerun'
    monkeypatch.setattr(src.experiment,'Experiment',Existing)
    monkeypatch.setattr(sys,'argv',['run_all.py','--root',str(tmp_path),'--mode','PILOT','--stage','all'])
    run_all.main()
    assert len(created)==1
    assert called==[('pilot-fixed','P5')]
