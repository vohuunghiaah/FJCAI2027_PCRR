"""Summarize measured local validation without fabricating scientific results."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import xml.etree.ElementTree as ET
import pandas as pd
from src.experiment import Experiment
from src.io import write_json, csv, versions

root=Path(__file__).resolve().parents[1]
exp=Experiment(root,'SMOKE')
exp.verify_freeze()
assert all(exp.state[f'P{i}']=='PASS' for i in range(1,5))
assert exp.state['P5']=='NOT_RUN'
assert not (exp.out/'test_access.json').exists()
tests=[]
for name in ['core_tests.xml','integration_tests.xml']:
    tree=ET.parse(root/'reports'/name)
    cases=tree.findall('.//testcase')
    assert all(c.find('failure') is None and c.find('error') is None for c in cases)
    tests.append((name,len(cases)))
total=sum(n for _,n in tests)
write_json(root/'results/local_validation.json',{'tests':dict(tests),'smoke_experiment':exp.id,
    'smoke_status':exp.state,'real_test_evaluated':False,'versions':versions()})
headers={
 'summary.csv':['dataset','model','B','condition','level','scorer','aurc_mean','aurc_std','augrc_mean','delta_aurc_mean'],
 'per_seed_results.csv':['dataset','model','seed','B','condition','level','scorer','target_coverage','aurc','augrc','realized_coverage','realized_selective_risk'],
 'metrics_by_corruption.csv':['dataset','model','condition','level','scorer','B','target_coverage','aurc'],
 'ablation_results.csv':['dataset','model','B','condition','level','scorer','aurc_mean'],
 'statistical_summary.csv':['dataset','model','condition_group','scorer','mean_paired_delta_aurc','std_across_seeds','ci95_low','ci95_high']}
for name,columns in headers.items():
    if not (root/'results'/name).exists(): csv(root/'results'/name,pd.DataFrame(columns=columns))
if not (root/'results/frozen_protocol.json').exists():
    write_json(root/'results/frozen_protocol.json',{'status':'NOT_RUN','scope':'FULL',
        'reason':'No real FULL P4 run; this is a status placeholder, not an executable freeze.',
        'development_freeze':str((exp.out/'frozen_protocol.json').relative_to(root))})
text=f'''# Local implementation acceptance — 2026-11-09

Implementation validation: **PASS**. Scientific FULL acceptance: **NOT_RUN**.

## Executed evidence

- Existing workspace read/write probe succeeded on `G:\\My Drive\\FJCAI2027_PCRR`.
- Three UCI raw datasets passed file reading, expected row/feature/class counts, exact label sets and manifest SHA-256 verification. No raw data or download notebook was changed.
- `{total}` tests passed: {tests}. XML evidence is in `reports/`.
- Tests include known-answer metrics, tied scores, threshold boundaries, corruption determinism, ECDF split guards, train-only preprocessing, checkpoint reload for all three models, temporal label-independent duplicate purging, synthetic FULL P1–P5 (including statistics/figures), freeze tamper detection, and a SMOKE Test-access guard.
- Real Dry Bean SMOKE `{exp.id}`: P1/P2/P3/P4 PASS; P5 NOT_RUN by design. LR and MLP used seed 42, Model-Val checkpoint selection, clean/C1/C2 Risk-Val and clean Calibration. Development outputs are not paper evidence.
- All three datasets' split logic checked across five seeds. Bank split identical for every seed; four cross-boundary duplicate rows purged. Class presence checked in each split.
- Five notebook schemas and Python cell syntax validated. Notebook Colab execution itself has not been performed here.
- Synthetic P5 generated PNG/PDF charts; a representative risk–coverage PNG was visually inspected. Synthetic data outputs remain in temporary test directories and are not copied into research result tables.

## Bugs found and resolved

Float32 MLP softmax roundoff initially triggered sklearn probability warnings. Validated probabilities are now normalized in float64. Reload comparison normalizes both predictions before comparison; real SMOKE was rerun after the fix. Prior experiment IDs are retained rather than overwritten.

Third-party Matplotlib/pyparsing deprecation warnings may remain; there are no corresponding test failures.

## Artifact paths

- `src/`: data, preprocessing, models, corruptions, CPCR, risk baselines, calibration, metrics, stage orchestration and scientific reporting.
- `configs/`: dataset, model, corruption and experiment settings.
- `notebooks/`: five Colab notebooks.
- `results/{exp.id}/`: actual local development evidence and immutable development freeze.
- `checkpoints/{exp.id}/`: fitted preprocessors are embedded in saved models; MLP resume state and Model-Val logs are preserved.
- `results/dataset_readiness.json`, `raw_data_audit.csv`, `split_validation_all_seeds.csv`, `local_validation.json`.
- `reports/core_tests.xml`, `integration_tests.xml`, `METHODOLOGY.md`.

## Reproduction commands

```bash
python -m pytest -q
python scripts/validate_workspace.py
python run_all.py --mode SMOKE --stage all
```

Read README for Colab mount/install/restart and PILOT → FULL stages. Full result CSVs currently contain headers only. `results/frozen_protocol.json` is explicitly NOT_RUN until FULL P4; the real SMOKE freeze is stored under its experiment ID.

## Limitations and remaining acceptance

- PILOT and real FULL have not run; RF on real datasets, Rice training, Bank training, five-seed scientific comparisons and real Test results are NOT_RUN.
- Real Test records were partitioned/audited as required by P1 but never used for model predictions, method selection or reported scientific metrics.
- Local writes were verified through the mounted Drive filesystem. Remote synchronization and Colab visibility have not been independently verified.
- FULL bootstrap costs and GPU training are not benchmarked locally. Epoch state and condition caches support resume; do not run concurrent writers for the same experiment.
- Group-aware stratification slightly changes nominal row ratios. Bank duplicate purging changes effective counts. See methodology for exact policies and statistical caveats.
- No conclusion about CPCR novelty, superiority, C3 transfer or deployment value is justified until FULL is run and reviewed.

Proceed to PILOT only after reviewing SMOKE evidence. Proceed to scientific P5 only after FULL P1–P4 PASS and an intact FULL freeze. Root acceptance documents summarize the local delivery; per-experiment reports/status files are authoritative for subsequent runs.
'''
for file in ['IMPLEMENTATION.md','FINAL_ACCEPTANCE.md']:
    (root/'reports'/file).write_text(text,encoding='utf-8')
(root/'reports/P5_ACCEPTANCE.md').write_text('''# P5 acceptance

Status: **NOT_RUN** for real scientific evaluation.

Work implemented: FULL-only verified-freeze gate, all conditions and scorers, B ablations, paired cluster bootstrap, CSV summaries, PNG/PDF figures and scientific reporting.

Artifacts: `src/evaluation.py`, `src/experiment.py`, `notebooks/05_P5_final_evaluation.ipynb`. Real result tables have headers only until FULL P5 runs.

Test command: `python -m pytest tests/test_integration.py -q`. Synthetic P1–P5 execution and freeze-tamper tests passed; see integration_tests.xml. No real Test result is claimed.

Errors: none outstanding in executed synthetic validation. Limits: no real FULL run, no Colab execution verified. The rounding/reload issue discovered during SMOKE was fixed and retested; see IMPLEMENTATION.md.

Transition: run FULL P1–P4 with matching settings, review its freeze, then run FULL P5. Scientific acceptance requires reviewing real metrics, intervals, costs and limitations, even when execution completes successfully.
''',encoding='utf-8')
print(f'Acceptance reports written. {total} tests passed. SMOKE: {exp.id}; real P5 NOT_RUN.')
