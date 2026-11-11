# P1 Acceptance — pilot-0c42a7ee168ac5f3

Status: **PASS**

## Work and evidence

All three raw datasets passed hashes, shapes and labels. Split disjointness and train-only transformer reload checks passed. Test was partitioned and persisted, not evaluated.

## Artifacts

- results/pilot-0c42a7ee168ac5f3/
- data/processed/pilot-0c42a7ee168ac5f3/
- checkpoints/pilot-0c42a7ee168ac5f3/

## Verification

`python -m pytest -q`

Stage command: `python run_all.py --mode PILOT --stage P1`

Stage PASS refers to executed runtime assertions; unit-test evidence is recorded separately in reports/IMPLEMENTATION.md.

## Limits and next gate

SMOKE/PILOT are development-only, not publication evidence. P5 requires FULL and verified P4 artifacts. Scientific acceptance requires inspection of actual results.
