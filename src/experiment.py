"""Stage orchestration with content-addressed experiments and immutable P4 freeze."""
import itertools
import logging
import os
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import yaml
from .io import sha256, digest, write_json, read_json, save, csv, versions, atomic
from .data import readiness, audit, prepare_features, split_indices, load_split, SPLITS
from .preprocessing import make_preprocessor
from .models import train
from .metrics import classification, probabilities, ranking, deployment
from .corruptions import Corruptor, instability, geometry_violations
from .cpcr import ConditionalECDF
from .risk_baselines import SCORERS, score
from .calibration import select, calibrate


class Experiment:
    def __init__(self, root, mode='SMOKE', bank=False):
        self.root = Path(root).resolve(); self.mode = mode.upper()
        if self.mode not in ('SMOKE', 'PILOT', 'FULL'): raise ValueError(mode)
        self.cfg = {n: yaml.safe_load((self.root/f'configs/{n}.yaml').read_text())
                    for n in ('datasets', 'models', 'corruption', 'experiments')}
        self.datasets = ['dry_bean'] if self.mode == 'SMOKE' else ['dry_bean', 'rice']
        if bank and self.mode == 'FULL': self.datasets.append('bank_marketing')
        self.seeds = self.cfg['experiments']['seeds'] if self.mode == 'FULL' else [42]
        self.models = ['lr', 'mlp'] if self.mode == 'SMOKE' else ['lr', 'rf', 'mlp']
        self.bs = self.cfg['corruption']['perturbations'] if self.mode == 'FULL' else [8]
        self.code_hashes = {str(p.relative_to(self.root)): sha256(p) for p in sorted((self.root/'src').glob('*.py'))}
        self.signature = {'mode': self.mode, 'datasets': self.datasets, 'config': self.cfg,
                          'code': self.code_hashes, 'raw_manifest': sha256(self.root/'data/raw/dataset_manifest.json'),
                          'versions': versions()}
        self.id = self.mode.lower()+'-'+digest(self.signature)[:16]
        self.out = self.root/'results'/self.id
        self.out.mkdir(parents=True, exist_ok=True)
        self.report_dir = self.root/'reports'/self.id; self.report_dir.mkdir(parents=True, exist_ok=True)
        (self.root/'logs').mkdir(exist_ok=True)
        logging.basicConfig(filename=self.root/'logs'/f'{self.id}.log', level=logging.INFO, force=True,
                            format='%(asctime)s %(levelname)s %(message)s')
        write_json(self.out/'experiment.json', self.signature)
        self.state = read_json(self.out/'status.json') if (self.out/'status.json').exists() else {f'P{i}': 'NOT_RUN' for i in range(1, 6)}

    def processed(self, dataset, seed):
        return self.root/'data/processed'/self.id/dataset/str(0 if dataset == 'bank_marketing' else seed)

    def checkpoint(self, dataset, model, seed):
        return self.root/'checkpoints'/self.id/dataset/model/str(seed)

    def combos(self): return itertools.product(self.datasets, self.models, self.seeds)

    def conditions(self, development=False):
        values = [('clean', 0.)]
        for k in ('missing', 'gaussian', 'quantization'):
            if development and k == 'quantization': continue
            levels = self.cfg['corruption'][k]
            if self.mode != 'FULL': levels = [levels[1]]
            values.extend((k, v) for v in levels)
        return values

    def report(self, stage, status, detail):
        self.state[stage] = status; write_json(self.out/'status.json', self.state)
        body = (f'# {stage} Acceptance — {self.id}\n\nStatus: **{status}**\n\n'
                f'## Work and evidence\n\n{detail}\n\n'
                f'## Artifacts\n\n- results/{self.id}/\n- data/processed/{self.id}/\n- checkpoints/{self.id}/\n'
                f'\n## Verification\n\n`python -m pytest -q`\n\n'
                f'Stage command: `python run_all.py --mode {self.mode} --stage {stage}`\n\n'
                'Stage PASS refers to executed runtime assertions; unit-test evidence is recorded separately in reports/IMPLEMENTATION.md.\n\n'
                '## Limits and next gate\n\nSMOKE/PILOT are development-only, not publication evidence. '
                'P5 requires FULL and verified P4 artifacts. Scientific acceptance requires inspection of actual results.\n')
        for p in [self.report_dir/f'{stage}_ACCEPTANCE.md', self.root/'reports'/f'{stage}_ACCEPTANCE.md']:
            atomic(p, lambda q: q.write_text(body, encoding='utf-8'))

    def run(self, stage):
        number = int(stage[1:])
        if number > 1 and self.state[f'P{number-1}'] != 'PASS':
            raise RuntimeError(f'{stage} blocked: previous stage not PASS for {self.id}')
        if stage == 'P5' and self.mode != 'FULL':
            self.development_report()
            self.report(stage, 'NOT_RUN', 'Development results exported. Scientific P5 not run: this mode never predicts Test.')
            return
        if self.state.get('P5') == 'PASS' and stage != 'P5':
            raise RuntimeError('Completed Test experiment is immutable; use its existing artifacts')
        if stage in ('P1','P2','P3') and (self.out/'frozen_protocol.json').exists():
            raise RuntimeError('P4 freeze exists; upstream artifacts are immutable')
        logging.info('START %s', stage)
        try:
            detail = getattr(self, stage.lower())()
            self.report(stage, 'PASS', detail)
            logging.info('PASS %s', stage)
        except Exception as e:
            self.report(stage, 'FAIL', f'{type(e).__name__}: {e}')
            logging.exception(stage)
            raise

    def p1(self):
        frames, evidence = readiness(self.root, self.cfg['datasets'])
        write_json(self.out/'dataset_readiness.json', {'status': 'DATASET_READY', 'datasets': evidence})
        rows, summaries, schemas = [], [], {}
        for dataset in self.datasets:
            raw, labels = frames[dataset]; rows.append(audit(raw, labels, dataset))
            X = prepare_features(raw, dataset)
            schemas[dataset] = {'types': X.dtypes.astype(str).to_dict(), 'raw_geometry': geometry_violations(raw),
                                'labels': self.cfg['datasets'][dataset]['labels'],
                                'bank_pdays': '999 -> NaN plus previously_contacted category; unknown retained',
                                'duplicate_policy': 'Group-identical features; temporal cross-boundary duplicates purged'}
            y = labels.map({c: i for i, c in enumerate(self.cfg['datasets'][dataset]['labels'])}).to_numpy()
            seeds = [self.seeds[0]] if dataset == 'bank_marketing' else self.seeds
            for seed in seeds:
                ids, purged = split_indices(X, y, seed, dataset == 'bank_marketing')
                dest = self.processed(dataset, seed); dest.mkdir(parents=True, exist_ok=True)
                split_path = self.root/'data/splits'/self.id/dataset/f'{0 if dataset == "bank_marketing" else seed}.json'
                write_json(split_path, {'indices': ids, 'purged': purged, 'seed': None if dataset == 'bank_marketing' else seed})
                for split in SPLITS:
                    ix = ids[split]
                    save(dest/f'{split}.joblib', {'X': X.iloc[ix].copy(), 'y': y[ix], 'row_id': ix})
                    summaries.append({'dataset': dataset, 'seed': 0 if dataset == 'bank_marketing' else seed,
                                      'split': split, 'rows': len(ix), 'fraction': len(ix)/len(y),
                                      'class_counts': pd.Series(y[ix]).value_counts().to_json(), 'purged': len(purged)})
                for scaled in (True, False):
                    prep = make_preprocessor(X.iloc[ids['train']], scaled).fit(X.iloc[ids['train']])
                    z = prep.transform(X.iloc[ids['train']]); assert np.isfinite(z).all()
                    path = dest/f'preprocessor_{scaled}.joblib'; save(path, prep)
                    np.testing.assert_array_equal(z, joblib.load(path).transform(X.iloc[ids['train']]))
                save(dest/'corruptor.joblib', Corruptor().fit(X.iloc[ids['train']]))
        csv(self.out/'data_audit.csv', pd.DataFrame(rows)); csv(self.out/'split_summary.csv', pd.DataFrame(summaries))
        write_json(self.out/'feature_schema.json', schemas)
        for f in ('data_audit.csv', 'split_summary.csv', 'feature_schema.json'):
            atomic(self.root/'results'/f, lambda p, f=f: p.write_bytes((self.out/f).read_bytes()))
        self.publish_hashes('p1', list((self.root/'data/processed'/self.id).rglob('*.joblib')) + list((self.root/'data/splits'/self.id).rglob('*.json')))
        return 'All three raw datasets passed hashes, shapes and labels. Split disjointness and train-only transformer reload checks passed. Test was partitioned and persisted, not evaluated.'

    def publish_hashes(self, name, paths):
        hashes = {str(p.relative_to(self.root)): sha256(p) for p in paths}
        write_json(self.out/f'{name}_hashes.json', hashes)
        return hashes

    def verify_hashes(self, hashes):
        for rel, expected in hashes.items():
            if sha256(self.root/rel) != expected: raise RuntimeError(f'Artifact integrity mismatch: {rel}')

    def p2(self):
        self.verify_hashes(read_json(self.out/'p1_hashes.json'))
        metrics = []
        for ds, kind, seed in self.combos():
            path = self.processed(ds, seed); d = load_split(path, 'train'); v = load_split(path, 'model_val')
            cp = self.checkpoint(ds, kind, seed); cp.mkdir(parents=True, exist_ok=True)
            model_path = cp/'model.joblib'; meta_path = cp/'model.json'
            if model_path.exists() and meta_path.exists():
                meta = read_json(meta_path)
                if sha256(model_path) != meta['sha256']: raise RuntimeError('Checkpoint checksum mismatch')
                model = joblib.load(model_path); elapsed = meta['seconds']
            else:
                prep = joblib.load(path/f'preprocessor_{kind != "rf"}.joblib')
                model, elapsed = train(kind, prep, d['X'], d['y'], v['X'], v['y'], self.cfg['models'][kind], seed, cp)
                save(model_path, model)
                write_json(meta_path, {'sha256': sha256(model_path), 'seconds': elapsed, 'config': self.cfg['models'][kind]})
            p = probabilities(model.predict_proba(v['X']))
            np.testing.assert_allclose(p, probabilities(joblib.load(model_path).predict_proba(v['X'])), atol=1e-7)
            save(cp/'model_val_predictions.joblib', {'p': p, 'y': v['y'], 'row_id': v['row_id']})
            result = classification(v['y'], p)
            write_json(cp/'model_val_metrics.json', result)
            metrics.append({'dataset': ds, 'model': kind, 'seed': seed, 'seconds': elapsed,
                            **{k: val for k, val in result.items() if k != 'confusion_matrix'}})
        csv(self.out/'model_val_metrics.csv', pd.DataFrame(metrics))
        self.publish_hashes('p2', list((self.root/'checkpoints'/self.id).rglob('model.joblib')))
        return f'{len(metrics)} models loaded and validated on Model-Val. No Test predictions.'

    def features(self, ds, kind, seed, split, condition, B, model, corruptor, ecdf=None, allow_test=False):
        data = load_split(self.processed(ds, seed), split, allow_test=allow_test)
        noise_seed = int(digest([ds, seed, split, condition])[:8], 16)
        X = corruptor.transform(data['X'], *condition, noise_seed)
        start = time.perf_counter(); p = probabilities(model.predict_proba(X)); inference = time.perf_counter()-start
        start = time.perf_counter()
        v = instability(model, X, corruptor, B, self.cfg['corruption']['perturbation_sigma'], noise_seed+100, p)
        u = 1-p.max(1); q = ecdf.transform(u, v) if ecdf is not None else np.zeros(len(u))
        overhead = time.perf_counter()-start
        return {'p': p, 'v': v, 'q': q, 'u': u, 'errors': (p.argmax(1) != data['y']).astype(int),
                'row_id': data['row_id'], 'y': data['y'], 'split': split, 'kind': condition[0], 'level': condition[1],
                'inference_seconds': inference, 'perturbation_seconds': overhead,
                'manifest': {'seed': noise_seed, 'condition': condition, 'B': B, 'geometry_violations': geometry_violations(X)}}

    def p3(self):
        self.verify_hashes(read_json(self.out/'p2_hashes.json'))
        manifests = []
        for ds, kind, seed in self.combos():
            cp = self.checkpoint(ds, kind, seed); model = joblib.load(cp/'model.joblib')
            corruptor = joblib.load(self.processed(ds, seed)/'corruptor.joblib')
            for B in self.bs:
                ref = self.features(ds, kind, seed, 'model_val', ('clean', 0), B, model, corruptor)
                ecdf = ConditionalECDF(self.cfg['experiments']['uncertainty_bins'], self.cfg['experiments']['min_bin_size']).fit(ref['u'], ref['v'])
                save(cp/f'ecdf_B{B}.joblib', ecdf)
                dev = [self.features(ds, kind, seed, 'risk_val', c, B, model, corruptor, ecdf) for c in self.conditions(True)]
                for item in dev:
                    assert np.isfinite(item['q']+item['v']).all()
                    manifests.append({'dataset': ds, 'model': kind, 'seed': seed, **item['manifest']})
                save(cp/f'development_B{B}.joblib', dev)
        write_json(self.out/'corruption_manifests.json', manifests)
        self.publish_hashes('p3', list((self.root/'checkpoints'/self.id).rglob('ecdf_*.joblib')) + list((self.root/'checkpoints'/self.id).rglob('development_*.joblib')))
        return 'Model-Val ECDF references and clean/C1/C2 Risk-Val features persisted. C3 excluded from selection; corruption unit tests cover C3.'

    def p4(self):
        frozen_path = self.out/'frozen_protocol.json'
        if frozen_path.exists():
            self.verify_freeze(); return 'Existing immutable protocol verified.'
        for stage in ('p1', 'p2', 'p3'): self.verify_hashes(read_json(self.out/f'{stage}_hashes.json'))
        selections, searches = [], []
        for ds, kind, seed in self.combos():
            cp = self.checkpoint(ds, kind, seed); model = joblib.load(cp/'model.joblib')
            corruptor = joblib.load(self.processed(ds, seed)/'corruptor.joblib')
            for B in self.bs:
                ecdf = joblib.load(cp/f'ecdf_B{B}.joblib'); dev = joblib.load(cp/f'development_B{B}.joblib')
                cal = self.features(ds, kind, seed, 'calibration', ('clean', 0), B, model, corruptor, ecdf)
                for scorer in SCORERS:
                    chosen, grid = select(scorer, dev, self.cfg['experiments']['grid'])
                    s = score(scorer, cal['p'], cal['v'], cal['q'], chosen['lambda'], chosen['gamma'])
                    identity = {'dataset': ds, 'model': kind, 'seed': seed, 'B': B, 'scorer': scorer}
                    selections.append({**identity, **chosen, 'thresholds': calibrate(s, self.cfg['experiments']['coverage'])})
                    searches.extend({**identity, **r} for r in grid)
        csv(self.out/'parameter_search.csv', pd.DataFrame(searches))
        hashes = {}
        for stage in ('p1', 'p2', 'p3'): hashes.update(read_json(self.out/f'{stage}_hashes.json'))
        frozen = {'experiment_id': self.id, 'signature': self.signature, 'artifact_hashes': hashes,
                  'selections': selections, 'development_conditions': self.conditions(True),
                  'ecdf': {'fit_split': 'model_val', 'fallback': 'pooled Model-Val ECDF for sparse bins',
                           'bins': self.cfg['experiments']['uncertainty_bins'], 'min_bin_size': self.cfg['experiments']['min_bin_size']},
                  'inference_device': 'cpu', 'test_opened': False}
        write_json(frozen_path, frozen)
        write_json(self.out/'frozen_protocol.sha256.json', {'sha256': sha256(frozen_path)})
        if self.mode == 'FULL':
            write_json(self.root/'results/frozen_protocol.json', frozen)
        self.development_report()
        return 'Risk parameters selected on Risk-Val; clean Calibration thresholds frozen with code, library and artifact hashes.'

    def verify_freeze(self):
        path = self.out/'frozen_protocol.json'
        if sha256(path) != read_json(self.out/'frozen_protocol.sha256.json')['sha256']: raise RuntimeError('Frozen protocol altered')
        frozen = read_json(path)
        if digest(frozen['signature']) != digest(self.signature): raise RuntimeError('Protocol/configuration mismatch')
        self.verify_hashes(frozen['artifact_hashes'])
        readiness(self.root, self.cfg['datasets'])
        return frozen

    def development_report(self):
        frozen = self.verify_freeze(); rows = []
        for item in frozen['selections']:
            cp = self.checkpoint(item['dataset'], item['model'], item['seed'])
            for d in joblib.load(cp/f'development_B{item["B"]}.joblib'):
                s = score(item['scorer'], d['p'], d['v'], d['q'], item['lambda'], item['gamma'])
                rows.append({k: item[k] for k in ('dataset','model','seed','B','scorer')} |
                            {'condition': d['kind'], 'level': d['level'], **ranking(d['errors'], s)})
        csv(self.out/'development_results.csv', pd.DataFrame(rows))

    def p5(self):
        if self.mode != 'FULL': raise PermissionError('Test evaluation only in FULL')
        frozen = self.verify_freeze()
        write_json(self.out/'test_access.json', {'experiment': self.id, 'opened_after_p4': True})
        rows = []
        for ds, kind, seed in self.combos():
            cp = self.checkpoint(ds, kind, seed); model = joblib.load(cp/'model.joblib')
            corruptor = joblib.load(self.processed(ds, seed)/'corruptor.joblib')
            for B in self.bs:
                ecdf = joblib.load(cp/f'ecdf_B{B}.joblib')
                selected = [s for s in frozen['selections'] if (s['dataset'],s['model'],s['seed'],s['B']) == (ds,kind,seed,B)]
                for cond in self.conditions():
                    key = f'{ds}_{kind}_{seed}_B{B}_{cond[0]}_{cond[1]}'
                    dest = self.out/'predictions'/f'{key}.joblib'; receipt = dest.with_suffix('.json')
                    if dest.exists() and receipt.exists():
                        if sha256(dest) != read_json(receipt)['sha256']: raise RuntimeError('Prediction cache corrupted')
                        result = joblib.load(dest)
                    else:
                        d = self.features(ds, kind, seed, 'test', cond, B, model, corruptor, ecdf, allow_test=True)
                        result = {'features': d, 'scores': {}, 'metrics': []}
                        for item in selected:
                            start = time.perf_counter()
                            s = score(item['scorer'], d['p'], d['v'], d['q'], item['lambda'], item['gamma'])
                            score_time = time.perf_counter()-start
                            result['scores'][item['scorer']] = s
                            rank = ranking(d['errors'], s)
                            for target, threshold in item['thresholds'].items():
                                result['metrics'].append({'dataset': ds, 'model': kind, 'seed': seed, 'B': B,
                                    'condition': cond[0], 'level': cond[1], 'scorer': item['scorer'],
                                    'target_coverage': float(target), 'threshold': threshold,
                                    'development_aurc': item['development_aurc'],
                                    'inference_seconds': d['inference_seconds'],
                                    'risk_seconds': score_time + (0 if item['scorer'] in ('msp','entropy','margin','no_q','uncertainty_only') else d['perturbation_seconds']),
                                    **rank, **deployment(d['errors'], s, threshold)})
                        result['classification'] = classification(d['y'], d['p'])
                        save(dest, result); write_json(receipt, {'sha256': sha256(dest)})
                    rows.extend(result['metrics'])
        from .evaluation import summarize
        summarize(pd.DataFrame(rows), self.out, self.cfg['experiments'])
        for file in ('summary.csv','per_seed_results.csv','metrics_by_corruption.csv','ablation_results.csv','statistical_summary.csv'):
            atomic(self.root/'results'/file, lambda p, file=file: p.write_bytes((self.out/file).read_bytes()))
        return f'FULL evaluation completed: {len(list(self.combos()))*len(self.conditions())} primary dataset/model/seed/condition cells; B=4/16 are separate ablations. See scientific_report.md.'
