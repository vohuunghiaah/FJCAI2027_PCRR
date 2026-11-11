import numpy as np
from .metrics import ranking
from .risk_baselines import score


def candidates(name, grid):
    if name in ('cpcr', 'raw_instability'): return [(a, b) for a in grid for b in grid]
    if name in ('weighted', 'no_interaction'): return [(a, 0.) for a in grid]
    return [(0., 0.)]


def select(name, development, grid):
    """Equal-weight mean AURC over prespecified clean/C1/C2 Risk-Val conditions."""
    if any(d['split'] != 'risk_val' or d['kind'] == 'quantization' for d in development):
        raise PermissionError('Selection only permits Risk-Val clean/C1/C2')
    rows = []
    for lam, gamma in candidates(name, grid):
        val = np.mean([ranking(d['errors'], score(name, d['p'], d['v'], d['q'], lam, gamma))['aurc'] for d in development])
        rows.append({'lambda': lam, 'gamma': gamma, 'development_aurc': float(val)})
    return min(rows, key=lambda r: (r['development_aurc'], r['lambda'], r['gamma'])), rows


def calibrate(scores, coverages, split='calibration'):
    if split != 'calibration': raise PermissionError('Thresholds require clean Calibration')
    s = np.asarray(scores)
    if not len(s) or not np.isfinite(s).all(): raise ValueError('Invalid calibration scores')
    # Exact ceil(n*c) order statistic; <= includes ties and may exceed target.
    return {str(c): float(np.sort(s)[min(len(s)-1, int(np.ceil(c*len(s)))-1)]) for c in coverages}
