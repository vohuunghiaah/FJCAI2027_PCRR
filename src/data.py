"""Readiness gate and deterministic splits; raw files are never modified."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.io import arff
from sklearn.model_selection import train_test_split
from .io import read_json, sha256

SPLITS = ('train', 'model_val', 'risk_val', 'calibration', 'test')


def read_frame(path):
    if path.suffix.lower() == '.arff':
        frame = pd.DataFrame(arff.loadarff(path)[0])
        for c in frame.select_dtypes('object'):
            frame[c] = frame[c].map(lambda v: v.decode() if isinstance(v, bytes) else v)
        return frame
    if path.suffix.lower() in ('.xlsx', '.xls'): return pd.read_excel(path)
    return pd.read_csv(path, sep=';' if 'bank' in path.name else ',')


def readiness(root, config):
    raw = Path(root) / 'data/raw'
    try:
        manifest = read_json(raw / 'dataset_manifest.json')
        frames, evidence = {}, []
        for name, spec in config.items():
            entry = manifest['datasets'][name]
            path = (raw / entry['raw_file']).resolve()
            if not path.is_relative_to(raw.resolve()): raise ValueError('Raw path outside workspace')
            if sha256(path) != entry['sha256']: raise ValueError(f'{name}: SHA-256 mismatch')
            f = read_frame(path)
            label = next((c for c in f if c.lower() in ('class', 'y')), None)
            if label is None: raise ValueError(f'{name}: missing label')
            y = f.pop(label)
            if len(f) != spec['rows'] or f.shape[1] != spec['features']:
                raise ValueError(f'{name}: unexpected shape {f.shape}')
            if y.isna().any() or set(y) != set(spec['labels']): raise ValueError(f'{name}: invalid labels')
            if name == 'bank_marketing' and path.name != 'bank-additional-full.csv':
                raise ValueError('Bank requires bank-additional-full.csv')
            frames[name] = (f, y)
            evidence.append({'dataset': name, 'file': str(path), 'format': path.suffix,
                             'rows': len(f), 'features': f.shape[1], 'classes': y.nunique(), 'sha256': entry['sha256']})
        return frames, evidence
    except Exception as e:
        raise RuntimeError(f'DATASET_NOT_READY: {e}') from e


def prepare_features(X, dataset):
    X = X.copy()
    if dataset == 'bank_marketing':
        X = X.drop(columns=['duration'])
        X['previously_contacted'] = (X.pdays != 999).astype(str)
        X['pdays'] = X.pdays.replace(999, np.nan)
    return X.replace([np.inf, -np.inf], np.nan)


def audit(X, y, name):
    numeric = X.select_dtypes('number')
    groups = pd.util.hash_pandas_object(X, index=False)
    conflicts = pd.DataFrame({'g': groups, 'y': y}).groupby('g').y.nunique().gt(1).sum()
    return {'dataset': name, 'rows': len(X), 'missing': int(X.isna().sum().sum()),
            'infinite': int(np.isinf(numeric.to_numpy()).sum()),
            'duplicates': int(X.duplicated().sum()), 'conflicting_feature_groups': int(conflicts),
            'constant_features': ','.join(c for c in X if X[c].nunique(dropna=False) <= 1),
            'class_counts': y.value_counts().to_json(), 'types': X.dtypes.astype(str).to_json()}


def split_indices(X, y, seed, temporal=False):
    """Duplicate feature groups cannot straddle splits. Temporal duplicates are purged.

    Random: stratify unique feature groups, then expand; proportions may differ
    slightly at row level. Conflicting-label groups stop the experiment.
    """
    groups = pd.util.hash_pandas_object(X, index=False).to_numpy()
    g = pd.DataFrame({'g': groups, 'y': np.asarray(y)})
    if not temporal and g.groupby('g').y.nunique().max() > 1:
        raise ValueError('Conflicting labels in identical feature groups; resolve before P1')
    if temporal:
        cuts = (np.array([0, .6, .7, .8, .9, 1]) * len(y)).astype(int)
        seen, out, purged = set(), {}, []
        for i, key in enumerate(SPLITS):
            ids = np.arange(cuts[i], cuts[i+1])
            keep = np.array([groups[j] not in seen for j in ids])
            out[key] = ids[keep]
            purged.extend(ids[~keep].tolist())
            seen.update(groups[ids].tolist())
    else:
        unique = g.drop_duplicates('g')
        rest = unique.index.to_numpy()
        out, purged = {}, []
        for key, fraction in zip(SPLITS[:-1], [.6, .25, 1/3, .5]):
            selected, rest = train_test_split(rest, train_size=fraction, random_state=seed,
                                              stratify=np.asarray(y)[rest])
            out[key] = np.flatnonzero(np.isin(groups, groups[selected]))
        out['test'] = np.flatnonzero(np.isin(groups, groups[rest]))
    for i, a in enumerate(SPLITS):
        for b in SPLITS[i+1:]:
            assert not set(groups[out[a]]) & set(groups[out[b]])
    assert sum(map(len, out.values())) + len(purged) == len(y)
    return out, purged


def load_split(path, split, *, allow_test=False):
    if split == 'test' and not allow_test:
        raise PermissionError('Test access requires verified P4 freeze and FULL P5')
    import joblib
    return joblib.load(Path(path) / f'{split}.joblib')
