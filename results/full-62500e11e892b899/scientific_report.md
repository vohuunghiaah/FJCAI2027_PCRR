# Scientific evaluation

Computed from frozen FULL Test evaluation. Negative paired AURC differences favor the scorer.

Bank extension: included

## Prespecified questions

### bank_marketing / lr

1. CPCR minus MSP AURC: -0.0116239.
2. CPCR minus weighted raw instability: -0.00109919.
3. Conditional ECDF contribution (CPCR minus raw): -0.00111697.
4. Interaction contribution (CPCR minus no interaction): -0.000290326.
5. Seed paired differences: {13: -0.011459772385743383, 21: -0.013020952127016127, 42: -0.009418554045638383, 87: -0.014246196132245875, 101: -0.009973856761668865}; inspect clustered CIs in statistical_summary.csv.
6. Held-out C3 mean delta versus MSP: -0.00483011.
7. CPCR scoring/base inference time ratio (CPU inference): 10.9. Suitability depends on deployment budget.
8. Selected Risk-Val mean AURC: 0.106294; Test mean: 0.445016. Different condition mixes prevent attributing this gap solely to overfitting.

### bank_marketing / mlp

1. CPCR minus MSP AURC: -0.037847.
2. CPCR minus weighted raw instability: -0.046693.
3. Conditional ECDF contribution (CPCR minus raw): -0.0466825.
4. Interaction contribution (CPCR minus no interaction): -2.60337e-05.
5. Seed paired differences: {13: 0.0037840943508838376, 21: -0.05179542542655828, 42: -0.05856039622905222, 87: -0.0533245565385172, 101: -0.0293385220350376}; inspect clustered CIs in statistical_summary.csv.
6. Held-out C3 mean delta versus MSP: -0.0665828.
7. CPCR scoring/base inference time ratio (CPU inference): 10.5. Suitability depends on deployment budget.
8. Selected Risk-Val mean AURC: 0.118974; Test mean: 0.527956. Different condition mixes prevent attributing this gap solely to overfitting.

### bank_marketing / rf

1. CPCR minus MSP AURC: 0.
2. CPCR minus weighted raw instability: 3.84664e-06.
3. Conditional ECDF contribution (CPCR minus raw): 3.53079e-06.
4. Interaction contribution (CPCR minus no interaction): 0.
5. Seed paired differences: {13: 0.0, 21: 0.0, 42: 0.0, 87: 0.0, 101: 0.0}; inspect clustered CIs in statistical_summary.csv.
6. Held-out C3 mean delta versus MSP: 0.
7. CPCR scoring/base inference time ratio (CPU inference): 8.76. Suitability depends on deployment budget.
8. Selected Risk-Val mean AURC: 0.0989065; Test mean: 0.413027. Different condition mixes prevent attributing this gap solely to overfitting.

### dry_bean / lr

1. CPCR minus MSP AURC: 0.
2. CPCR minus weighted raw instability: -2.82828e-07.
3. Conditional ECDF contribution (CPCR minus raw): -3.06224e-08.
4. Interaction contribution (CPCR minus no interaction): 0.
5. Seed paired differences: {13: 0.0, 21: 0.0, 42: 0.0, 87: 0.0, 101: 0.0}; inspect clustered CIs in statistical_summary.csv.
6. Held-out C3 mean delta versus MSP: 0.
7. CPCR scoring/base inference time ratio (CPU inference): 34.5. Suitability depends on deployment budget.
8. Selected Risk-Val mean AURC: 0.0221343; Test mean: 0.0181608. Different condition mixes prevent attributing this gap solely to overfitting.

### dry_bean / mlp

1. CPCR minus MSP AURC: 0.
2. CPCR minus weighted raw instability: 3.46302e-07.
3. Conditional ECDF contribution (CPCR minus raw): 2.37325e-07.
4. Interaction contribution (CPCR minus no interaction): 0.
5. Seed paired differences: {13: 0.0, 21: 0.0, 42: 0.0, 87: 0.0, 101: 0.0}; inspect clustered CIs in statistical_summary.csv.
6. Held-out C3 mean delta versus MSP: 0.
7. CPCR scoring/base inference time ratio (CPU inference): 31. Suitability depends on deployment budget.
8. Selected Risk-Val mean AURC: 0.0202484; Test mean: 0.0168042. Different condition mixes prevent attributing this gap solely to overfitting.

### dry_bean / rf

1. CPCR minus MSP AURC: -0.00107813.
2. CPCR minus weighted raw instability: -0.000961765.
3. Conditional ECDF contribution (CPCR minus raw): -0.000943027.
4. Interaction contribution (CPCR minus no interaction): -0.00107813.
5. Seed paired differences: {13: -0.001641149999346323, 21: -0.0008808030876300485, 42: -0.0008572560518326262, 87: -0.0009025162798130204, 101: -0.0011089401644935382}; inspect clustered CIs in statistical_summary.csv.
6. Held-out C3 mean delta versus MSP: 0.000100523.
7. CPCR scoring/base inference time ratio (CPU inference): 9.51. Suitability depends on deployment budget.
8. Selected Risk-Val mean AURC: 0.0175864; Test mean: 0.0157024. Different condition mixes prevent attributing this gap solely to overfitting.

### rice / lr

1. CPCR minus MSP AURC: 1.24433e-05.
2. CPCR minus weighted raw instability: 1.15599e-05.
3. Conditional ECDF contribution (CPCR minus raw): 1.17058e-05.
4. Interaction contribution (CPCR minus no interaction): 1.24433e-05.
5. Seed paired differences: {13: 0.0, 21: 4.8899760703892056e-05, 42: 0.0, 87: 1.3316555808309382e-05, 101: 0.0}; inspect clustered CIs in statistical_summary.csv.
6. Held-out C3 mean delta versus MSP: 6.28806e-05.
7. CPCR scoring/base inference time ratio (CPU inference): 28. Suitability depends on deployment budget.
8. Selected Risk-Val mean AURC: 0.0138106; Test mean: 0.0110506. Different condition mixes prevent attributing this gap solely to overfitting.

### rice / mlp

1. CPCR minus MSP AURC: 6.24486e-05.
2. CPCR minus weighted raw instability: 6.36641e-05.
3. Conditional ECDF contribution (CPCR minus raw): 6.36641e-05.
4. Interaction contribution (CPCR minus no interaction): 6.24486e-05.
5. Seed paired differences: {13: 0.00028606016621573853, 21: 0.0, 42: 0.0, 87: 2.618272637800968e-05, 101: 0.0}; inspect clustered CIs in statistical_summary.csv.
6. Held-out C3 mean delta versus MSP: 9.1508e-05.
7. CPCR scoring/base inference time ratio (CPU inference): 27. Suitability depends on deployment budget.
8. Selected Risk-Val mean AURC: 0.0143184; Test mean: 0.0111453. Different condition mixes prevent attributing this gap solely to overfitting.

### rice / rf

1. CPCR minus MSP AURC: -0.000167598.
2. CPCR minus weighted raw instability: -0.000149792.
3. Conditional ECDF contribution (CPCR minus raw): -0.000148767.
4. Interaction contribution (CPCR minus no interaction): -0.000167598.
5. Seed paired differences: {13: 3.496421169006444e-05, 21: -0.0005875745530243077, 42: 0.0001988792647487801, 87: -0.0005618685127424946, 101: 7.761182861993413e-05}; inspect clustered CIs in statistical_summary.csv.
6. Held-out C3 mean delta versus MSP: 0.000157145.
7. CPCR scoring/base inference time ratio (CPU inference): 9.37. Suitability depends on deployment budget.
8. Selected Risk-Val mean AURC: 0.0218787; Test mean: 0.01805. Different condition mixes prevent attributing this gap solely to overfitting.

## Interpretation limits

No novelty or superiority is assumed. All variants were tuned before Test. Intervals condition on fitted models and observed split design, preserve repeated original-row identity and paired scorers, and use temporal blocks for Bank. They do not measure uncertainty from new training datasets. Dataset/model results remain separate; no pseudo-replicated pooled significance test. Observation corruption does not guarantee physically realizable geometry. Failure AUROC and selective risk are undefined for single-class errors and zero accepted samples respectively.