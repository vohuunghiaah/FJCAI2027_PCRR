# PILOT safety audit — 2026-11-09

Audited run: `pilot-0c42a7ee168ac5f3`. This is a read-only audit of its scientific artifacts; no experiment was rerun or source module modified.

## 1. Preservation of prior results: qualified, not absolute

`run_all.py` creates one Experiment object and skips any stage already marked PASS when `--stage all` is used. Dataset splits, processed files and checkpoints are namespaced by experiment ID. The earlier `pilot-54a0b3496e1a4491` directory still exists with P1–P3 PASS.

For the audited run, all 36 artifact hashes recorded in its frozen protocol match current files. The frozen protocol's own checksum also matches. The current `src/*.py` hashes match the recorded source signature.

The earlier run's 36 artifacts also match its recorded P1/P2/P3 hashes. No mismatch was found in either run.

However, the command is NOT a no-write operation: construction rewrites `experiment.json`; development-mode P5 regenerates `development_results.csv`, status and P5 acceptance reports. Root-level convenience copies such as `results/data_audit.csv`, `results/split_summary.csv`, `results/feature_schema.json`, and `reports/P*_ACCEPTANCE.md` can be replaced by another run. Incomplete stages can rewrite their own partial artifacts on resume. Logs append. These are not immutable archives.

Therefore, preservation of completed, experiment-scoped checkpoints/splits/freeze is supported; the stronger claim that no previous file is ever overwritten is false. Cite the per-experiment paths, not shared convenience copies.

## 2. PILOT does not train, calibrate or evaluate on Test

P2 reads Train and Model-Val. P3 builds the reference on Model-Val and development features on Risk-Val. P4 selects using Risk-Val and calibrates with clean Calibration. PILOT's P5 branch only exports development results and sets scientific P5 to NOT_RUN. The actual Test evaluation function requires FULL.

The audited directory has neither `test_access.json` nor a `predictions/` directory. Its status records P1–P4 PASS and P5 NOT_RUN. Test-access guards are tested with synthetic SMOKE and PILOT runs; see `pilot_safety_tests.xml`.

P1 does read/audit the complete raw dataset, stratifies its labels to create partitions, and persists the held-out Test split. Integrity verification also reads serialized Test bytes to compute hashes. These operations are distinct from fitting, calibration, prediction or scoring on Test; claiming that Test data is never read at all would be inaccurate.

## 3. One experiment ID for P1–P4: verified

All P1–P4 acceptance reports, the frozen protocol and all 36 recorded artifact paths use `pilot-0c42a7ee168ac5f3`. One log records sequential PASS for P1, P2, P3 and P4. `run_all.py` constructs the Experiment once, outside its stage loop.

This holds for the completed `--stage all` invocation. Separate invocations can receive a new ID if source/configuration/manifest/library/Python versions change, as happened during the Python 3.13.16 → 3.13.18 transition.

## Regression command

```bash
python -m pytest tests/test_runner.py tests/test_integration.py -k "stage_all or development_modes" -q --junitxml=reports/pilot_safety_tests.xml
```

The added tests do not modify `src/`, configuration, or the audited run's experiment signature.

Executed result: **3 passed, 3 deselected**, 63.41 seconds. The selected tests cover completed-stage skipping with one Experiment instance and guarded synthetic end-to-end SMOKE/PILOT execution.
