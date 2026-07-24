# Paper-to-Code Map

| Paper concept | Artifact location |
|---|---|
| SafetyPool archival source | `02_source_code/policies/safetypool.py` |
| SafetyPool modular source | `02_source_code/policies/safetypool_components/` |
| Modular compatibility launcher | `02_source_code/policies/safetypool_modular.py` |
| Internal run identifier | `Karthikeya27adv8` in policy source and raw metadata |
| Canonical baselines | `02_source_code/training/train_canonical_baselines.py` |
| Evaluation protocol | `03_configuration/experimental_protocol.json` |
| Complete SafetyPool results | `04_data/raw/safetypool/` |
| Complete baseline results | `04_data/raw/baselines/` |
| Collision RMST computation | `restricted_mean_survival_time()` in `generate_ieee_results.py` |
| Maximum-step completion | `metric_vector()` in `generate_ieee_results.py` |
| Seed-level results | `04_data/processed/seed_level_metrics.csv` |
| IQM and bootstrap intervals | `04_data/processed/aggregate_metrics.csv` |
| Wilcoxon/Holm tests | `04_data/processed/statistical_tests.csv` |
| Per-seed figures | `05_results/comparisons/seed_<N>/` |
| Aggregate figures | `05_results/comparisons/aggregate/` |

## Statistical unit

The matched **training seed** is the unit of statistical inference. Each
seed-level metric is calculated from 300 test episodes. The 23 paired
seed-level values are then compared with a two-sided Wilcoxon signed-rank test.
The three baseline comparisons are Holm-corrected separately for each metric.

## Fair-test controls

Every method is evaluated on scenario seeds 100000–100299 with a 500-step cap.
The trained networks are frozen for evaluation. The raw result records are
validated for seed identity, scenario coverage, and test-episode count before
analysis.
