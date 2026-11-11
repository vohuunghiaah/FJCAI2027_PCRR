# Local implementation acceptance — 2026-11-09

Implementation validation: **PASS**. Scientific FULL acceptance: **NOT_RUN**.

## Executed evidence

- Existing workspace read/write probe succeeded on `G:\My Drive\FJCAI2027_PCRR`.
- Three UCI raw datasets passed file reading, expected row/feature/class counts, exact label sets and manifest SHA-256 verification. No raw data or download notebook was changed.
- `18` tests passed: [('core_tests.xml', 16), ('integration_tests.xml', 2)]. XML evidence is in `reports/`.
- Tests include known-answer metrics, tied scores, threshold boundaries, corruption determinism, ECDF split guards, train-only preprocessing, checkpoint reload for all three models, temporal label-independent duplicate purging, synthetic FULL P1–P5 (including statistics/figures), freeze tamper detection, and a SMOKE Test-access guard.
- Real Dry Bean SMOKE `smoke-0b7d7669ba2bae59`: P1/P2/P3/P4 PASS; P5 NOT_RUN by design. LR and MLP used seed 42, Model-Val checkpoint selection, clean/C1/C2 Risk-Val and clean Calibration. Development outputs are not paper evidence.
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
- `results/smoke-0b7d7669ba2bae59/`: actual local development evidence and immutable development freeze.
- `checkpoints/smoke-0b7d7669ba2bae59/`: fitted preprocessors are embedded in saved models; MLP resume state and Model-Val logs are preserved.
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
