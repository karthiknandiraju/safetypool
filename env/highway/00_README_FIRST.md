# SafetyPool Highway Package

This directory is the HighwayEnv companion to the repository's `metadrive/`
directory. It contains the Highway-only framework, configuration, data, and
Collision Restricted Mean Survival Time (RMST) results extracted from
`CombinedDataHighwayMeta`.

## Contents

- `02_source_code/` — Highway policies, canonical DQN baselines, comparison
  scripts, environment adapter, smoke test, and Collision RMST analysis.
- `03_configuration/` — Python requirements, environment information, and the
  supplied validation notes.
- `04_data/` — Highway Collision RMST episode data and aggregate CSV files for
  all 23 matched training seeds.
- `05_results/` — Highway Collision RMST figures, recomputed outputs, and
  paper-facing tables.
- `06_checksums/` — original archive checksums plus package checksums and a
  generated validation report.

## Included seeds

`3, 5, 7, 9, 13, 17, 27, 33, 38, 42, 45, 48, 54, 63, 65, 67, 69, 73, 76, 77, 93, 108, 111`

There are exactly 23 per-seed episode-data directories.

## Evaluation protocol represented by the data

- Environment: HighwayEnv `highway-v0`
- Methods: SafetyPool, Epsilon-Greedy DQN, NoisyNet DQN, and DQN with Random
  Network Distillation (RND)
- Training: 500 episodes per seed
- Frozen-policy testing: 300 episodes per seed
- Test horizon: 500 agent-decision steps per episode
- Primary reported outcome: autonomous-vehicle Collision RMST

## Naming note

Some source files retain historical internal experiment names such as
`Karthikeya27adv8956` and `Karthikeya27adv23`. They are preserved to keep the
supplied framework, output paths, manifests, and archived results reproducible.
The research-facing algorithm name is **SafetyPool**.

## Quick checks

```bash
python -m py_compile 02_source_code/*.py 02_source_code/policies/*.py
python 02_source_code/smoke_test_highway.py
sha256sum -c 06_checksums/SHA256SUMS.txt
```

See `02_source_code/README.md` and `03_configuration/ENVIRONMENT.md` for the
original execution details.
