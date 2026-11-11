# P1 Acceptance — full-d635c35778ca1554

Status: **PASS**

## Work and evidence

All three raw datasets passed hashes, shapes and labels. Split disjointness and train-only transformer reload checks passed. Test was partitioned and persisted, not evaluated.

## Artifacts

- results/full-d635c35778ca1554/
- data/processed/full-d635c35778ca1554/
- checkpoints/full-d635c35778ca1554/

## Verification

`python -m pytest -q`

Stage command: `python run_all.py --mode FULL --stage P1`

Stage PASS refers to executed runtime assertions; unit-test evidence is recorded separately in reports/IMPLEMENTATION.md.

## Limits and next gate

SMOKE/PILOT are development-only, not publication evidence. P5 requires FULL and verified P4 artifacts. Scientific acceptance requires inspection of actual results.
