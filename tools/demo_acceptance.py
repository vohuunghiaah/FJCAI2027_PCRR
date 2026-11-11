"""Demo Model-Val only; loads verified frozen LR checkpoint, never trains."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import joblib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'02_MA_NGUON'))
from src.metrics import probabilities
from src.corruptions import instability
from src.cpcr import cpcr
def main():
    d=ROOT/'DEMO'; metadata=json.loads((d/'metadata.json').read_text())
    for name,h in metadata['hashes'].items():
        assert hashlib.sha256((d/name).read_bytes()).hexdigest()==h,name
    model=joblib.load(d/'model.joblib'); corruptor=joblib.load(d/'corruptor.joblib')
    ecdf=joblib.load(d/'ecdf_B8.joblib'); data=joblib.load(d/'model_val.joblib')
    X=data['X'].iloc[:8]; p=probabilities(model.predict_proba(X))
    perturbed=corruptor.transform(X,'gaussian',.01,2027)
    u=1-p.max(1); v=instability(model,X,corruptor,B=8,sigma=.01,seed=2027,base=p)
    q=ecdf.transform(u,v); selected=metadata['selection']
    risk=cpcr(u,q,selected['lambda'],selected['gamma']); threshold=selected['thresholds']['0.9']
    assert np.isfinite(risk).all()
    print('DEMO MODEL-VAL: khong phai ket qua Test; khong huan luyen.')
    print('Mau dau:',X.iloc[0].to_dict()); print('Mau nhieu nhe:',perturbed.iloc[0].to_dict())
    print('Xac suat:',p.tolist())
    print('lambda, gamma:',selected['lambda'],selected['gamma'],'threshold:',threshold)
    for i in range(len(X)):
        print({'row_id':int(data['row_id'][i]),'prediction':metadata['labels'][p[i].argmax()],'u':float(u[i]),'v':float(v[i]),'q':float(q[i]),'CPCR':float(risk[i]),'accept':bool(risk[i]<=threshold)})
    print('Thu hang MSP:',np.argsort(u,kind='stable').tolist())
    print('Thu hang CPCR:',np.argsort(risk,kind='stable').tolist())
    # A separate, explicitly pedagogical example to expose the interaction.
    assert np.isclose(cpcr([.2],[.5],.25,.5)[0],.375)
    print('Vi du tinh tay (khong la du lieu nghien cuu): .2 + .25*.5 + .5*.2*.5 = .375')
if __name__=='__main__': main()
