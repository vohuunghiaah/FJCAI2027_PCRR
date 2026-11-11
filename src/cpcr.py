import numpy as np


class ConditionalECDF:
    def __init__(self, bins=10, min_size=20):
        self.bins, self.min_size = bins, min_size

    def fit(self, u, v, split='model_val'):
        if split != 'model_val': raise PermissionError('ECDF reference must be Model-Val')
        u, v = np.asarray(u), np.asarray(v)
        if not len(u) or u.shape != v.shape or not np.isfinite(u+v).all(): raise ValueError('Invalid reference')
        self.edges = np.unique(np.quantile(u, np.linspace(0, 1, self.bins+1)[1:-1]))
        ids = np.searchsorted(self.edges, u, side='right')
        self.global_values = np.sort(v)
        self.values = [np.sort(v[ids == i]) for i in range(len(self.edges)+1)]
        return self

    def transform(self, u, v):
        u, v = np.asarray(u), np.asarray(v); out = np.empty_like(v, dtype=float)
        ids = np.searchsorted(self.edges, u, side='right')
        for i, values in enumerate(self.values):
            if len(values) < self.min_size: values = self.global_values
            mask = ids == i
            out[mask] = np.searchsorted(values, v[mask], side='right') / len(values)
        if not np.isfinite(out).all(): raise ValueError('Nonfinite ECDF')
        return out


def cpcr(u, q, lam, gamma):
    if lam < 0 or gamma < 0: raise ValueError('Risk coefficients must be nonnegative')
    return np.asarray(u) + lam*np.asarray(q) + gamma*np.asarray(u)*np.asarray(q)
