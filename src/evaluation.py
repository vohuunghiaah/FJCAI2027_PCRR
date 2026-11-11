"""Paired original-row cluster bootstrap; seeds are repeated measurements."""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from .io import csv, atomic
from .metrics import ranking, curve


def paired_cluster_bootstrap(records, scorer, replicates=1000, seed=2027):
    """Resample original row IDs once per replicate across all seeds/conditions.

    Within each dataset/model, repeat appearances of a row have identical weight.
    For temporal Bank data, resample contiguous blocks of the ordered test IDs.
    Returns a conditional empirical interval, not an IID-seed significance test.
    """
    ids = np.unique(np.concatenate([r['features']['row_id'] for r in records]))
    positions = [np.searchsorted(ids, r['features']['row_id']) for r in records]
    temporal = records[0].get('temporal', False)
    rng = np.random.default_rng(seed); differences = []
    block = max(2, int(np.ceil(np.sqrt(len(ids)))))
    for _ in range(replicates):
        if temporal:
            starts = rng.integers(len(ids), size=int(np.ceil(len(ids)/block)))
            sampled = ((starts[:, None]+np.arange(block)) % len(ids)).ravel()[:len(ids)]
        else: sampled = rng.integers(len(ids), size=len(ids))
        counts = np.bincount(sampled, minlength=len(ids)); vals = []
        for r, pos in zip(records, positions):
            take = np.repeat(np.arange(len(pos)), counts[pos])
            if not len(take): continue
            e = r['features']['errors'][take]
            vals.append(curve(e, r['scores'][scorer][take])[1].mean() - curve(e, r['scores']['msp'][take])[1].mean())
        differences.append(np.mean(vals))
    return np.quantile(differences, [.025, .975]).tolist()


def summarize(frame, out, config):
    out = Path(out)
    keys = ['dataset','model','seed','B','condition','level','target_coverage']
    base = frame[frame.scorer == 'msp'][keys+['aurc']].rename(columns={'aurc':'msp_aurc'})
    frame = frame.merge(base, on=keys, validate='many_to_one')
    frame['delta_aurc_msp'] = frame.aurc-frame.msp_aurc
    csv(out/'per_seed_results.csv', frame)
    one = frame[frame.target_coverage == .9]
    group = ['dataset','model','B','condition','level','scorer']
    summary = one.groupby(group).agg(aurc_mean=('aurc','mean'), aurc_std=('aurc','std'),
                augrc_mean=('augrc','mean'), delta_aurc_mean=('delta_aurc_msp','mean'),
                failure_auroc_mean=('failure_auroc','mean'), seeds=('seed','nunique')).reset_index()
    csv(out/'summary.csv', summary)
    csv(out/'metrics_by_corruption.csv', frame.groupby(['dataset','model','condition','level','scorer','B','target_coverage']).mean(numeric_only=True).reset_index())
    csv(out/'ablation_results.csv', summary[summary.scorer.isin(['cpcr','no_q','no_interaction','uncertainty_only','instability_only','raw_instability'])])
    stats = []
    for (ds, model), part in one[one.B == 8].groupby(['dataset','model']):
        records = []
        for path in (out/'predictions').glob(f'{ds}_{model}_*_B8_*.joblib'):
            r = joblib.load(path); r['temporal'] = ds == 'bank_marketing'; records.append(r)
        for condition_group in ('all', 'quantization'):
            chosen = [r for r in records if condition_group == 'all' or r['features']['kind'] == condition_group]
            subset = part if condition_group == 'all' else part[part.condition == condition_group]
            for scorer in sorted(set(part.scorer)-{'msp'}):
                ci = paired_cluster_bootstrap(chosen, scorer, config['bootstrap_replicates'], config['bootstrap_seed'])
                values = subset[subset.scorer == scorer].groupby('seed').delta_aurc_msp.mean()
                stats.append({'dataset': ds, 'model': model, 'condition_group': condition_group, 'scorer': scorer,
                              'mean_paired_delta_aurc': values.mean(), 'std_across_seeds': values.std(),
                              'ci95_low': ci[0], 'ci95_high': ci[1], 'replicates': config['bootstrap_replicates'],
                              'unit': 'temporal circular blocks' if ds == 'bank_marketing' else 'original row cluster',
                              'interpretation': 'conditional empirical CI; seeds not independent; no multiplicity-adjusted significance claim'})
        csv(out/'statistical_summary.csv', pd.DataFrame(stats))
    figures(frame, out)
    report(frame, pd.DataFrame(stats), out)


def figures(frame, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    directory = out/'figures'; directory.mkdir(exist_ok=True)
    def export(fig, name):
        fig.tight_layout(); fig.savefig(directory/f'{name}.png', dpi=300); fig.savefig(directory/f'{name}.pdf'); plt.close(fig)
    data = frame[(frame.B == 8) & (frame.target_coverage == .9)]
    for (ds, model), part in data.groupby(['dataset','model']):
        prefix = f'{ds}_{model}'
        for metric, title in [('aurc','AURC (lower is better)'), ('realized_selective_risk','Fixed calibration threshold: selective risk'), ('risk_seconds','Risk scoring seconds')]:
            fig, ax = plt.subplots(figsize=(10,4))
            part.groupby('scorer')[metric].mean().plot.bar(ax=ax); ax.set_ylabel(title)
            export(fig, prefix+'_'+metric)
        fig, axes = plt.subplots(1,3,figsize=(13,4))
        for ax, cond in zip(axes, ('missing','gaussian','quantization')):
            for scorer in ('msp','weighted','cpcr'):
                p = part[(part.condition == cond) & (part.scorer == scorer)].groupby('level').aurc.mean()
                ax.plot(p.index, p.values, marker='o', label=scorer)
            ax.set(title=cond, xlabel='Severity', ylabel='AURC'); ax.legend()
        export(fig, prefix+'_severity')
        allpart = frame[(frame.dataset == ds)&(frame.model == model)&(frame.scorer == 'cpcr')&(frame.target_coverage == .9)]
        fig, ax = plt.subplots(figsize=(5,4)); allpart.groupby('B').aurc.mean().plot.bar(ax=ax)
        ax.set_ylabel('CPCR AURC; separately tuned B'); export(fig, prefix+'_B_ablation')
        # Representative curves/distributions are explicitly labeled by seed and condition.
        paths = sorted((out/'predictions').glob(f'{ds}_{model}_*_B8_clean_*.joblib'))
        if paths:
            r = joblib.load(paths[0]); fig, ax = plt.subplots(figsize=(6,4))
            for scorer in ('msp','weighted','cpcr'):
                c, risk, _ = curve(r['features']['errors'], r['scores'][scorer]); ax.plot(c,risk,label=scorer)
            ax.set(xlabel='Test sorted coverage', ylabel='Selective risk', title=paths[0].stem); ax.legend(); export(fig,prefix+'_risk_coverage')
            fig, ax = plt.subplots(figsize=(6,4))
            for scorer in ('msp','cpcr'): ax.hist(r['scores'][scorer],bins=30,alpha=.5,label=scorer)
            ax.set_title(paths[0].stem); ax.legend(); export(fig,prefix+'_scores')


def report(frame, stats, out):
    main = frame[(frame.B == 8)&(frame.target_coverage == .9)]
    lines = ['# Scientific evaluation', '', 'Computed from frozen FULL Test evaluation. Negative paired AURC differences favor the scorer.', '',
             'Bank extension: '+('included' if 'bank_marketing' in set(main.dataset) else 'NOT RUN; conclusions limited to Dry Bean and Rice'), '',
             '## Prespecified questions', '']
    for (ds, model), p in main.groupby(['dataset','model']):
        means = p.groupby('scorer').aurc.mean()
        lines += [f'### {ds} / {model}', '',
            f'1. CPCR minus MSP AURC: {means["cpcr"]-means["msp"]:.6g}.',
            f'2. CPCR minus weighted raw instability: {means["cpcr"]-means["weighted"]:.6g}.',
            f'3. Conditional ECDF contribution (CPCR minus raw): {means["cpcr"]-means["raw_instability"]:.6g}.',
            f'4. Interaction contribution (CPCR minus no interaction): {means["cpcr"]-means["no_interaction"]:.6g}.']
        delta = p[p.scorer == 'cpcr'].groupby('seed').delta_aurc_msp.mean()
        c3 = p[(p.scorer == 'cpcr')&(p.condition == 'quantization')].delta_aurc_msp.mean()
        runtime = p[p.scorer == 'cpcr'].risk_seconds.sum()/p[p.scorer == 'cpcr'].inference_seconds.sum()
        dev = p[p.scorer == 'cpcr'].development_aurc.mean()
        lines += [f'5. Seed paired differences: {delta.to_dict()}; inspect clustered CIs in statistical_summary.csv.',
                  f'6. Held-out C3 mean delta versus MSP: {c3:.6g}.',
                  f'7. CPCR scoring/base inference time ratio (CPU inference): {runtime:.3g}. Suitability depends on deployment budget.',
                  f'8. Selected Risk-Val mean AURC: {dev:.6g}; Test mean: {means["cpcr"]:.6g}. Different condition mixes prevent attributing this gap solely to overfitting.', '']
    lines += ['## Interpretation limits', '', 'No novelty or superiority is assumed. All variants were tuned before Test. '
              'Intervals condition on fitted models and observed split design, preserve repeated original-row identity and paired scorers, '
              'and use temporal blocks for Bank. They do not measure uncertainty from new training datasets. '
              'Dataset/model results remain separate; no pseudo-replicated pooled significance test. '
              'Observation corruption does not guarantee physically realizable geometry. '
              'Failure AUROC and selective risk are undefined for single-class errors and zero accepted samples respectively.']
    atomic(out/'scientific_report.md', lambda p: p.write_text('\n'.join(lines), encoding='utf-8'))
