import numpy as np
from sklearn.metrics import accuracy_score, f1_score, log_loss, confusion_matrix, roc_auc_score


def probabilities(p):
    p = np.asarray(p, dtype=float)
    if p.ndim != 2 or not np.isfinite(p).all() or (p < 0).any(): raise ValueError('Invalid probabilities')
    if not np.allclose(p.sum(1), 1, atol=1e-5): raise ValueError('Probability rows must sum to one')
    # Float32 softmax can sum to 1 only within ~1e-7. Normalize in float64
    # after validation so log_loss's much tighter float64 tolerance is respected.
    return p / p.sum(axis=1, keepdims=True)


def classification(y, p, bins=15):
    p = probabilities(p)
    pred = p.argmax(1); conf = p.max(1); correct = pred == y
    ix = np.minimum((conf*bins).astype(int), bins-1)
    ece = sum(np.mean(ix == b)*abs(correct[ix == b].mean()-conf[ix == b].mean())
              for b in range(bins) if np.any(ix == b))
    return {'accuracy': accuracy_score(y, pred), 'macro_f1': f1_score(y, pred, average='macro', zero_division=0),
            'weighted_f1': f1_score(y, pred, average='weighted', zero_division=0),
            'nll': log_loss(y, p, labels=np.arange(p.shape[1])),
            'brier': np.mean(np.sum((p-np.eye(p.shape[1])[y])**2, axis=1)),
            'ece': ece, 'confusion_matrix': confusion_matrix(y, pred, labels=np.arange(p.shape[1])).tolist()}


def curve(errors, scores):
    """Expected cumulative errors for random tie breaking, discrete right sum."""
    e, s = np.asarray(errors, float), np.asarray(scores, float)
    if not len(e) or e.shape != s.shape or not np.isfinite(s).all(): raise ValueError('Invalid risk input')
    order = np.argsort(s, kind='stable'); e, s = e[order], s[order]
    starts = np.r_[0, np.flatnonzero(np.diff(s)) + 1]; ends = np.r_[starts[1:], len(s)]
    lengths = ends-starts
    sums = np.add.reduceat(e, starts)
    before = np.r_[0., np.cumsum(sums)[:-1]]
    cumulative = np.repeat(before, lengths) + (np.arange(len(e))-np.repeat(starts,lengths)+1)*np.repeat(sums/lengths,lengths)
    coverage = np.arange(1, len(e)+1)/len(e)
    return coverage, cumulative/np.arange(1, len(e)+1), cumulative/len(e)


def ranking(errors, scores):
    c, r, gr = curve(errors, scores)
    return {'aurc': float(r.mean()), 'augrc': float(gr.mean()),
            'failure_auroc': float(roc_auc_score(errors, scores)) if len(np.unique(errors)) == 2 else None,
            **{f'risk_at_{int(t*100)}': float(r[int(np.ceil(t*len(r)))-1]) for t in [.8, .9, .95]}}


def deployment(errors, scores, threshold):
    mask = np.asarray(scores) <= threshold
    return {'realized_coverage': float(mask.mean()),
            'realized_selective_risk': float(np.asarray(errors)[mask].mean()) if mask.any() else None,
            'accepted': int(mask.sum())}
