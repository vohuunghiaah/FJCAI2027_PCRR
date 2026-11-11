# P4 Acceptance — full-37245e523b162876

Status: **PASS**

## Work and evidence

Risk parameters selected on Risk-Val; clean Calibration thresholds frozen with code, library and artifact hashes.

## Artifacts

- results/full-37245e523b162876/
- data/processed/full-37245e523b162876/
- checkpoints/full-37245e523b162876/

## Verification

`python -m pytest -q`

Stage command: `python run_all.py --mode FULL --stage P4`

Stage PASS refers to executed runtime assertions; unit-test evidence is recorded separately in reports/IMPLEMENTATION.md.

## Limits and next gate

SMOKE/PILOT are development-only, not publication evidence. P5 requires FULL and verified P4 artifacts. Scientific acceptance requires inspection of actual results.
