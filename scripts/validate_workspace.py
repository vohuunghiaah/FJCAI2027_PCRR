"""Read-only raw validation and all-seed split QA; never predicts Test."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
import yaml
import nbformat
from src.data import readiness, prepare_features, audit, split_indices
from src.corruptions import geometry_violations
from src.io import write_json, csv

root=Path(__file__).resolve().parents[1]
config=yaml.safe_load((root/'configs/datasets.yaml').read_text())
frames, evidence=readiness(root,config)
rows=[]; summaries=[]
for name,(X,y) in frames.items():
    rows.append(audit(X,y,name))
    features=prepare_features(X,name)
    reference=None
    for seed in [13,21,42,87,101]:
        splits,purge=split_indices(features,y,seed,name=='bank_marketing')
        if name=='bank_marketing':
            signature={k:v.tolist() for k,v in splits.items()}
            if reference is not None: assert signature==reference
            reference=signature
        for split,ids in splits.items():
            assert len(ids)>0 and y.iloc[ids].nunique()==len(config[name]['labels'])
            summaries.append({'dataset':name,'seed':seed,'split':split,'n':len(ids),'purged':len(purge)})
    print(name,'READY; geometry:',geometry_violations(X))
for p in (root/'notebooks').glob('*.ipynb'):
    notebook=nbformat.read(p,as_version=4); nbformat.validate(notebook)
    for cell in notebook.cells:
        if cell.cell_type=='code': compile(cell.source,str(p),'exec')
write_json(root/'results/dataset_readiness.json',{'status':'DATASET_READY','datasets':evidence})
csv(root/'results/raw_data_audit.csv',pd.DataFrame(rows))
csv(root/'results/split_validation_all_seeds.csv',pd.DataFrame(summaries))
print('All datasets, all-seed split checks, and five notebook schemas/cell syntax passed; no Test predictions.')
