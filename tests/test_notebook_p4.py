import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
import pytest


@pytest.mark.parametrize('mode,bank', [('FULL',False),('FULL',True),('PILOT',False)])
def test_p4_notebook_respects_configuration(monkeypatch,tmp_path,mode,bank):
    notebook=json.loads((Path(__file__).resolve().parents[1]/'notebooks/04_P4_calibration.ipynb').read_text(encoding='utf-8'))
    calls=[]
    def fake_run(command,**kwargs):
        calls.append(command)
        return SimpleNamespace(stdout=f'Experiment: {mode.lower()}-fixture\nP4: PASS\n',check_returncode=lambda:None)
    monkeypatch.setattr(subprocess,'run',fake_run)
    scope={'ROOT':tmp_path,'MODE':mode,'BANK_EXTENSION':bank}
    exec(''.join(notebook['cells'][5]['source']),scope)
    assert len(calls)==1
    command=calls[0]
    assert command[command.index('--mode')+1]==mode
    assert command[command.index('--stage')+1]=='P4'
    assert ('--bank' in command)==bank
    assert scope['RUN_ID']==mode.lower()+'-fixture'
