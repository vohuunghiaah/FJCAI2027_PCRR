# P1 Acceptance — smoke-0b7d7669ba2bae59

Status: **PASS**

## Work and evidence

All three raw datasets passed hashes, shapes and labels. Split disjointness and train-only transformer reload checks passed. Test was partitioned and persisted, not evaluated.

## Artifacts

- results/smoke-0b7d7669ba2bae59/
- data/processed/smoke-0b7d7669ba2bae59/
- checkpoints/smoke-0b7d7669ba2bae59/

## Verification

`python -m pytest -q`

Stage command: `python run_all.py --mode SMOKE --stage P1`

Stage PASS refers to executed runtime assertions; unit-test evidence is recorded separately in reports/IMPLEMENTATION.md.

## Limits and next gate

SMOKE/PILOT are development-only, not publication evidence. P5 requires FULL and verified P4 artifacts. Scientific acceptance requires inspection of actual results.
