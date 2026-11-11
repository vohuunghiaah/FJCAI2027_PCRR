import numpy as np
from .cpcr import cpcr

SCORERS = ('msp', 'entropy', 'margin', 'instability', 'weighted', 'cpcr',
           'no_q', 'no_interaction', 'uncertainty_only', 'instability_only', 'raw_instability')


def score(name, p, v, q, lam=0., gamma=0.):
    u = 1-p.max(axis=1)
    if name in ('msp', 'no_q', 'uncertainty_only'): return u
    if name == 'entropy': return -np.sum(p*np.log(np.clip(p, 1e-15, 1)), axis=1)
    if name == 'margin':
        sorted_p = np.sort(p, axis=1)
        return 1-(sorted_p[:, -1]-sorted_p[:, -2])
    if name in ('instability', 'instability_only'): return v
    if name == 'weighted': return u+lam*v
    if name == 'no_interaction': return cpcr(u, q, lam, 0.)
    if name == 'raw_instability': return cpcr(u, v, lam, gamma)
    if name == 'cpcr': return cpcr(u, q, lam, gamma)
    raise ValueError(name)
