import hashlib
import json
import os
import platform
import tempfile
from pathlib import Path
from importlib.metadata import version
import joblib
import numpy as np


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def native(x):
    if isinstance(x, np.ndarray): return x.tolist()
    if isinstance(x, np.generic): return x.item()
    if isinstance(x, Path): return str(x)
    raise TypeError(type(x).__name__)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, default=native, allow_nan=False)


def digest(obj):
    return hashlib.sha256(canonical(obj).encode()).hexdigest()


def atomic(path, writer):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    os.close(fd)
    try:
        writer(Path(name))
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)


def write_json(path, obj):
    atomic(path, lambda p: p.write_text(json.dumps(obj, indent=2, default=native, allow_nan=False), encoding='utf-8'))


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, obj):
    atomic(path, lambda p: joblib.dump(obj, p))


def csv(path, frame):
    atomic(path, lambda p: frame.to_csv(p, index=False))


def versions():
    return {'python': platform.python_version(), **{p: version(p) for p in
        ['numpy', 'pandas', 'scipy', 'scikit-learn', 'torch', 'joblib', 'PyYAML']}}
