import argparse
import os
import json
from pathlib import Path


def prerequisite_message(exp, stage):
    previous = f'P{int(stage[1:])-1}'
    lines = [f'{stage} blocked: {previous} is not PASS for {exp.id}.']
    candidates = sorted((exp.root/'results').glob(f'{exp.mode.lower()}-*/experiment.json'),
                        key=lambda p: p.stat().st_mtime, reverse=True)
    for path in candidates:
        if path.parent == exp.out: continue
        state_path = path.parent/'status.json'
        if not state_path.exists(): continue
        saved = json.loads(path.read_text(encoding='utf-8'))
        state = json.loads(state_path.read_text(encoding='utf-8'))
        if state.get(previous) != 'PASS': continue
        lines.append(f'Earlier run {path.parent.name} has {previous}=PASS, but its experiment signature differs:')
        for key in sorted(set(saved) | set(exp.signature)):
            if saved.get(key) == exp.signature.get(key): continue
            if key == 'versions':
                old, new = saved[key], exp.signature[key]
                for package in sorted(set(old) | set(new)):
                    if old.get(package) != new.get(package):
                        lines.append(f'  {package}: {old.get(package)} -> {new.get(package)}')
            else: lines.append(f'  {key} changed')
        break
    lines += ['Existing artifacts are retained. Do not copy status files or bypass the freeze.',
              f'Rerun with the current environment: python run_all.py --mode {exp.mode}'
              f'{" --bank" if "bank_marketing" in exp.datasets else ""} --stage all',
              'SMOKE/PILOT never evaluate Test. FULL all includes P5 after its freeze gate.']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='PCRR stages P1–P5')
    parser.add_argument('--root', type=Path, default=Path(os.environ.get('PCRR_ROOT', Path(__file__).resolve().parent)))
    parser.add_argument('--mode', choices=['SMOKE','PILOT','FULL'], default='SMOKE')
    parser.add_argument('--stage', choices=['P1','P2','P3','P4','P5','all'], default='all')
    parser.add_argument('--bank', action='store_true')
    args = parser.parse_args()
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
    from src.experiment import Experiment
    exp = Experiment(args.root, args.mode, args.bank)
    print(f'Experiment: {exp.id}', flush=True)
    stages = [f'P{i}' for i in range(1,6)] if args.stage == 'all' else [args.stage]
    for stage in stages:
        if int(stage[1:]) > 1 and exp.state[f'P{int(stage[1:])-1}'] != 'PASS':
            parser.exit(1, prerequisite_message(exp, stage)+'\n')
        if args.stage == 'all' and exp.state[stage] == 'PASS':
            print(f'{stage}: completed; retaining existing artifacts', flush=True); continue
        print(f'{stage}: starting', flush=True); exp.run(stage)
        print(f'{stage}: {exp.state[stage]}', flush=True)
    print(f'Artifacts: {exp.out}', flush=True)


if __name__ == '__main__': main()
