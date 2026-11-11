# Prespecified methodology

## Data and splits

UCI sources: [Dry Bean](https://archive.ics.uci.edu/dataset/602/dry+bean+dataset), [Rice](https://archive.ics.uci.edu/dataset/545/rice+cammeo+and+osmancik), [Bank Marketing](https://archive.ics.uci.edu/dataset/222/bank+marketing). UCI explicitly identifies bank-additional-full.csv as ordered by date, May 2008–November 2010. The file does not provide full timestamps or client identifiers; date ordering is inherited, not independently reconstructed.

Readiness checks all records for format/shape/label/hash validation. P1 necessarily partitions and audits raw data, including future Test records; **no prediction, hyperparameter selection or fitted transformation uses Test in P1–P4**. This distinction is intentional.

Dry Bean contains 68 duplicate feature rows. Random datasets use stratified **unique feature groups** expanded back to rows. Nominal 60/10/10/10/10 proportions are therefore approximate; actual counts are reported. Exact feature groups cannot cross splits. Conflicting-label groups stop random splitting for review.

Bank drops duration and converts pdays=999 to missing plus a previously_contacted categorical indicator. It preserves unknown categories. Removing duration creates ambiguous feature groups (different labels are legitimate); these are audited rather than discarded using future labels. Temporal split boundaries remain fixed at 60/70/80/90% of original row order. Repeated feature groups appearing across boundaries are purged from later splits, using features only. Within-split repeats and ambiguous labels remain. Purged IDs and effective ratios are recorded. This avoids exact-feature overlap but cannot exclude repeated clients without client IDs. All five Bank model/noise seeds share one temporal split.

Imputers, scalers, encoders, corruption scales and ranges are fitted exclusively on Train. RF does not scale. Numeric missing values use Train median; categorical missingness uses Train mode, while unknown test categories encode to all zeros. The target schema is prespecified from UCI labels.

## Corruption and CPCR

C1 independently masks feature cells. C2 adds Gaussian error scaled by Train SD. C3 rounds numeric observations to steps of severity times Train range. C2/C3 clip to Train observed ranges and simple physical domains; categorical values are untouched. Train ranges are empirical constraints, not universal physical bounds. Pdays sentinel is converted before corruption. Geometric relationships (major/minor axes, convex/observed area, perimeter/area) are audited and violations recorded; derived measurements are not forced to describe a physically realizable grain. These experiments simulate observation errors.

All scorers and models share dataset/seed/split/condition noise seeds. B=4/8/16 use nested perturbation streams. The light perturbation is Gaussian with sigma=.01 on Train scales. It can leave missing cells missing. JS divergence uses natural logs, divided by ln(2), then averaged. Zero probabilities contribute zero.

Model-Val quantiles define uncertainty bins. Right-continuous conditional ECDF uses Model-Val instability values. A bin with fewer than 20 samples falls back to pooled Model-Val values. Duplicate quantile boundaries collapse. Scores increase with uncertainty/conditional rank for nonnegative grid coefficients.

Risk-Val objective is equal-weight mean AURC across prespecified clean and all C1/C2 levels in FULL; SMOKE/PILOT use .10 missing and .05 Gaussian. C3 is excluded from development selection. Ties select smaller lambda then gamma. Weighted raw instability tunes lambda on the same grid. No-interaction tunes lambda; raw-instability CPCR tunes both coefficients; B variants refit references, tune and calibrate separately before Test. No-q and uncertainty-only are identical by definition and intentionally labeled aliases.

## Metrics and thresholds

AURC = mean of selective error rates for k=1..n accepted samples. AUGRC = mean cumulative errors/n for k=1..n. Both are discrete right-endpoint sums. Equal scores receive expected cumulative errors under random tie ordering, avoiding dependence on original row order. Risk@coverage uses ceil(n*coverage); this is Test-ranked risk. Failure AUROC treats misclassification as positive and is undefined when all examples have the same correctness.

Thresholds are clean Calibration order statistics at ceil(n*target). Acceptance uses score <= threshold, includes all ties, and can exceed target coverage. Fixed thresholds remain unchanged under corruption. Realized coverage/risk are reported separately from Test-ranked metrics. Risk for zero accepted cases is undefined, not zero. Multiclass Brier sums squared class errors without dividing by class count; ECE uses 15 equal-width confidence bins.

## Statistical interpretation

Mean/std across five seeds are descriptive, not independent-sample inference. Paired bootstrap resamples original row IDs jointly across seed/condition/scorer appearances within each dataset/model, preserving shared corruption realizations. Bank uses circular blocks of ordered Test row IDs of length ceil(sqrt(n)). This is a fixed prespecified block heuristic, not estimated from Test outcomes. 1,000 replicates give percentile 95% intervals on paired mean AURC differences versus MSP. Report all-condition and held-out C3 estimates separately. Group comparisons remain dataset/model-specific; no pseudo-replicated pooled significance test.

These are conditional empirical intervals for already fitted models/splits. They do not capture uncertainty from collecting new training data; they are not multiplicity-adjusted proof of significance. FULL bootstrap and figures can be compute intensive. CPU inference and perturbation overhead include preprocessing; scorer arithmetic time is added separately. No claim about production latency on other hardware is warranted.
