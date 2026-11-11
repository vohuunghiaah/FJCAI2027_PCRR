import ast
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
import pytest
import nbformat


@pytest.mark.parametrize('completed', [False, True])
def test_p2_notebook_one_run_no_duplicate_training(monkeypatch, tmp_path, completed):
    path = Path(__file__).resolve().parents[1]/'notebooks/02_P2_baseline_training.ipynb'
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    pipelines = []
    for cell in notebook.cells:
        if cell.cell_type != 'code': continue
        tree = ast.parse(cell.source)
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'PIPELINE_CODE' for t in node.targets):
                pipelines.append(ast.literal_eval(node.value))
    assert len(pipelines) == 1
    created, executed, verified = [], [], []
    class FakeExperiment:
        def __init__(self, root, mode, bank):
            assert mode == 'FULL' and bank is False
            self.id = 'full-fixture'; self.out = tmp_path/self.id
            self.state = {s: 'PASS' if completed else 'NOT_RUN' for s in ('P1','P2')}
            created.append(self)
        def run(self, stage):
            assert stage in ('P1', 'P2')
            if stage == 'P2': assert self.state['P1'] == 'PASS'
            executed.append((self.id, stage)); self.state[stage] = 'PASS'
        def verify_hashes(self, hashes): verified.append(hashes)
    module = ModuleType('src.experiment'); module.Experiment = FakeExperiment
    io = ModuleType('src.io'); io.read_json = lambda path: path.name
    monkeypatch.setitem(sys.modules, 'src.experiment', module)
    monkeypatch.setitem(sys.modules, 'src.io', io)
    monkeypatch.setattr(sys, 'argv', ['-c', str(tmp_path), 'FULL', 'false'])
    exec(compile(pipelines[0], str(path), 'exec'), {})
    assert len(created) == 1
    assert executed == ([] if completed else [('full-fixture','P1'), ('full-fixture','P2')])
    assert verified == (['p1_hashes.json','p2_hashes.json'] if completed else [])
