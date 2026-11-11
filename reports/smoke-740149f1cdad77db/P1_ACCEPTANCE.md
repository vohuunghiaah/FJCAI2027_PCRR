# P1 Acceptance — smoke-740149f1cdad77db

Status: **PASS**

## Work and evidence

All three raw datasets passed hashes, shapes and labels. Split disjointness and train-only transformer reload checks passed. Test was partitioned and persisted, not evaluated.

## Artifacts

- results/smoke-740149f1cdad77db/
- data/processed/smoke-740149f1cdad77db/
- checkpoints/smoke-740149f1cdad77db/

## Verification

`python -m pytest -q`

Stage command: `python run_all.py --mode SMOKE --stage P1`

Stage PASS refers to executed runtime assertions; unit-test evidence is recorded separately in reports/IMPLEMENTATION.md.

## Limits and next gate

SMOKE/PILOT are development-only, not publication evidence. P5 requires FULL and verified P4 artifacts. Scientific acceptance requires inspection of actual results.
