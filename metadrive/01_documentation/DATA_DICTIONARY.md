# Data Dictionary

## Confirmatory metrics

### Collision RMST

**Collision restricted mean survival time (RMST)** is the area under the
Kaplan–Meier collision-free survival curve from step 0 through
`tau = 500`. A collision is the event; episodes without a collision by their
recorded endpoint are censored. Units are environment steps. Higher is better.

The implementation is
`02_source_code/analysis/generate_ieee_results.py::restricted_mean_survival_time`.

### Maximum-step completion

An episode is a maximum-step completion when `max_steps_reached` is true,
meaning it reached the full 500-step horizon. The seed-level rate is:

```text
number of maximum-step completions / 300 test episodes
```

Higher is better.

## Important raw episode columns

| Column | Meaning |
|---|---|
| `phase` | `train` or `test`; packaged comparisons use only `test`. |
| `seed` | Matched training seed. |
| `episode` | Episode index within the phase. |
| `scenario_seed` | Frozen evaluation scenario identifier. |
| `steps` | Number of environment steps in the episode. |
| `collision` | Whether a collision occurred. |
| `out_of_road` | Whether the vehicle left the drivable road. |
| `goal_reached` | Whether the environment goal was reached. |
| `max_steps_reached` | Whether the 500-step limit was reached. |
| `event_or_censor_time_steps` | Collision-event or censoring time used for RMST. |

## Processed tables

### `seed_level_metrics.csv`

One row per matched seed and method. In addition to the two confirmatory
metrics, it retains descriptive counts and source-file SHA-256 hashes.

### `aggregate_metrics.csv`

One row per metric and method. `iqm` is the 25%-trimmed interquartile mean
across the 23 matched seeds. `bootstrap_ci_low` and `bootstrap_ci_high` are the
2.5th and 97.5th percentiles of a deterministic seed bootstrap.

### `statistical_tests.csv`

One row per metric and baseline comparison. It includes the Wilcoxon statistic,
raw p-value, Holm-adjusted p-value, paper-reported p-value, and significance
indicator at alpha 0.05.

### `data_completeness.csv`

One row per seed–method file, documenting the validation status, episode count,
scenario range, and source path.

