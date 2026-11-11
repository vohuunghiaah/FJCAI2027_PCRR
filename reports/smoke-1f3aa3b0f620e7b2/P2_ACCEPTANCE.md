# P2 Acceptance — smoke-1f3aa3b0f620e7b2

Status: **FAIL**

## Work and evidence

AssertionError: 
Not equal to tolerance rtol=1e-07, atol=1e-07

Mismatched elements: 2 / 9513 (0.021%)
Max absolute difference among violations: 2.26651945e-07
Max relative difference among violations: 2.27440419e-07
 ACTUAL: array([[3.005172e-06, 4.062529e-06, 5.738076e-07, ..., 5.189756e-05,
        9.815658e-01, 2.034204e-04],
       [1.570767e-07, 6.390914e-08, 5.720313e-09, ..., 3.600219e-07,...
 DESIRED: array([[3.005172e-06, 4.062529e-06, 5.738076e-07, ..., 5.189757e-05,
        9.815658e-01, 2.034204e-04],
       [1.570767e-07, 6.390913e-08, 5.720313e-09, ..., 3.600219e-07,...

## Artifacts

- results/smoke-1f3aa3b0f620e7b2/
- data/processed/smoke-1f3aa3b0f620e7b2/
- checkpoints/smoke-1f3aa3b0f620e7b2/

## Verification

`python -m pytest -q`

Stage command: `python run_all.py --mode SMOKE --stage P2`

Stage PASS refers to executed runtime assertions; unit-test evidence is recorded separately in reports/IMPLEMENTATION.md.

## Limits and next gate

SMOKE/PILOT are development-only, not publication evidence. P5 requires FULL and verified P4 artifacts. Scientific acceptance requires inspection of actual results.
