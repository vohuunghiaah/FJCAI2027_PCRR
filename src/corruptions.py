"""Observation-error simulations, not guaranteed physically realizable objects."""
import numpy as np


def normalized(c): return c.lower().replace('_', '')


def geometry_violations(X):
    names = {normalized(c): c for c in X}
    out = {}
    for c in X.select_dtypes('number'):
        k = normalized(c)
        if k in ('area', 'perimeter', 'majoraxislength', 'minoraxislength', 'convexarea', 'equivdiameter'):
            out[c + '_nonpositive'] = int((X[c] <= 0).sum())
        if k in ('eccentricity', 'extent', 'solidity', 'roundness', 'compactness'):
            out[c + '_out_of_unit_interval'] = int(((X[c] < 0) | (X[c] > 1)).sum())
    for a, b in [('majoraxislength', 'minoraxislength'), ('convexarea', 'area')]:
        if a in names and b in names: out[a + '_lt_' + b] = int((X[names[a]] < X[names[b]]).sum())
    if all(k in names for k in ('area', 'perimeter')):
        out['isoperimetric_violation'] = int((X[names['perimeter']]**2 + 1e-5 < 4*np.pi*X[names['area']]).sum())
    return out


class Corruptor:
    def fit(self, X):
        self.columns = list(X.select_dtypes('number').columns)
        self.std = X[self.columns].std().fillna(0)
        self.lo = X[self.columns].min().fillna(0)
        self.hi = X[self.columns].max().fillna(0)
        return self

    def transform(self, X, kind, level, seed):
        rng = np.random.default_rng(seed); out = X.copy(deep=True)
        if kind == 'clean': return out
        if kind == 'missing':
            if not 0 <= level <= 1: raise ValueError('Missingness outside [0,1]')
            return out.mask(rng.random(out.shape) < level)
        if level < 0: raise ValueError('Negative severity')
        cols = self.columns
        values = out[cols].astype(float)
        if kind == 'gaussian': values += rng.normal(size=values.shape) * self.std.to_numpy() * level
        elif kind == 'quantization':
            step = ((self.hi-self.lo)*level).replace(0, 1)
            values = self.lo + np.round((values-self.lo)/step)*step
        else: raise ValueError(kind)
        values = values.clip(self.lo, self.hi, axis=1)
        out[cols] = values
        # Basic domain projection. Derived geometric relationships are audited,
        # not recomputed: these are independently corrupted sensor observations.
        for c in cols:
            k = normalized(c)
            if k in ('eccentricity', 'extent', 'solidity', 'roundness', 'compactness'):
                out[c] = out[c].clip(0, 1)
            if k in ('area', 'perimeter', 'majoraxislength', 'minoraxislength', 'convexarea', 'equivdiameter'):
                out[c] = out[c].clip(lower=np.finfo(float).eps)
        return out


def instability(model, X, corruptor, B=8, sigma=.01, seed=42, base=None):
    from .metrics import probabilities
    p = probabilities(model.predict_proba(X) if base is None else base)
    values = []
    for b in range(B):
        z = probabilities(model.predict_proba(corruptor.transform(X, 'gaussian', sigma, seed+b)))
        m = (p+z)/2
        # x log(x/m), with exact zero contribution at x=0.
        klp = np.sum(p * np.log(np.clip(p, 1e-15, 1)/np.clip(m, 1e-15, 1)), axis=1)
        klz = np.sum(z * np.log(np.clip(z, 1e-15, 1)/np.clip(m, 1e-15, 1)), axis=1)
        values.append(np.clip((klp+klz)/(2*np.log(2)), 0, 1))
    return np.mean(values, axis=0)
