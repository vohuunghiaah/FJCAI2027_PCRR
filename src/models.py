import copy
import random
import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from .io import atomic, csv


def seed_all(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(2)


class TabularModel:
    def __init__(self, preprocessor, estimator, kind, classes):
        self.preprocessor, self.estimator, self.kind, self.classes = preprocessor, estimator, kind, classes

    def predict_proba(self, X):
        z = self.preprocessor.transform(X).astype(np.float32)
        if self.kind != 'mlp':
            raw = self.estimator.predict_proba(z)
            out = np.zeros((len(z), self.classes))
            out[:, self.estimator.classes_.astype(int)] = raw
            return out
        self.estimator.eval()
        with torch.no_grad():
            return torch.cat([self.estimator(torch.from_numpy(z[i:i+2048])).softmax(1)
                              for i in range(0, len(z), 2048)]).numpy()


def train(kind, preprocessor, X, y, Xv, yv, cfg, seed, checkpoint_dir):
    seed_all(seed); start = time.perf_counter()
    z = preprocessor.transform(X).astype(np.float32)
    zv = preprocessor.transform(Xv).astype(np.float32)
    classes = int(max(y.max(), yv.max()))+1
    directory = Path(checkpoint_dir); directory.mkdir(parents=True, exist_ok=True)
    if kind != 'mlp':
        estimator = (LogisticRegression(**cfg, random_state=seed) if kind == 'lr'
                     else RandomForestClassifier(**cfg, random_state=seed))
        estimator.fit(z, y)
        logs = [{'training_seconds': time.perf_counter()-start, 'device': 'cpu'}]
    else:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        h1, h2 = cfg['hidden']
        estimator = nn.Sequential(nn.Linear(z.shape[1], h1), nn.ReLU(), nn.Linear(h1, h2),
                                  nn.ReLU(), nn.Linear(h2, classes)).to(device)
        optimizer = torch.optim.Adam(estimator.parameters(), lr=cfg['learning_rate'])
        loss_fn = nn.CrossEntropyLoss(); last = directory/'mlp_last.pt'
        best_loss, bad, begin, logs = float('inf'), 0, 0, []
        best = copy.deepcopy(estimator.state_dict())
        if last.exists():
            state = torch.load(last, map_location=device, weights_only=False)
            estimator.load_state_dict(state['model']); optimizer.load_state_dict(state['optimizer'])
            best, best_loss, bad, begin, logs = state['best'], state['best_loss'], state['bad'], state['epoch']+1, state['logs']
        tx, ty = torch.from_numpy(z).to(device), torch.tensor(y, dtype=torch.long, device=device)
        vx, vy = torch.from_numpy(zv).to(device), torch.tensor(yv, dtype=torch.long, device=device)
        for epoch in range(begin, cfg['epochs']):
            if bad >= cfg['patience']: break
            estimator.train()
            order = np.random.default_rng(seed+epoch).permutation(len(y)); total = 0.
            for offset in range(0, len(y), cfg['batch_size']):
                ix = torch.tensor(order[offset:offset+cfg['batch_size']], device=device)
                optimizer.zero_grad(); loss = loss_fn(estimator(tx[ix]), ty[ix]); loss.backward(); optimizer.step()
                total += loss.item()*len(ix)
            estimator.eval()
            with torch.no_grad(): val = loss_fn(estimator(vx), vy).item()
            if not np.isfinite(val): raise RuntimeError('Nonfinite MLP loss')
            if val < best_loss:
                best_loss, bad, best = val, 0, copy.deepcopy(estimator.state_dict())
            else: bad += 1
            logs.append({'epoch': epoch+1, 'train_loss': total/len(y), 'model_val_loss': val, 'device': device})
            state = {'model': estimator.state_dict(), 'optimizer': optimizer.state_dict(),
                     'best': best, 'best_loss': best_loss, 'bad': bad, 'epoch': epoch, 'logs': logs}
            atomic(last, lambda p: torch.save(state, p))
        estimator.load_state_dict(best); estimator = estimator.cpu()
    csv(directory/'training_log.csv', pd.DataFrame(logs))
    return TabularModel(preprocessor, estimator, kind, classes), time.perf_counter()-start
