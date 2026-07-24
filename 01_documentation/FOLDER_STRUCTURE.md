# Folder Structure

The numeric prefixes keep the review path stable after extraction.

## `01_documentation`

- `FOLDER_STRUCTURE.md` — this directory map.
- `CHANGELOG.md` — changes made after the original reproducibility release.
- `MODULAR_POLICY_ARCHITECTURE.md` — reusable policy component map, dependency
  flow, compatibility contract, and verification.
- `PAPER_TO_CODE_MAP.md` — mapping between paper terminology and files.
- `DATA_DICTIONARY.md` — definitions for the two confirmatory metrics and
  important CSV fields.
- `REPRODUCIBILITY_CHECKLIST.md` — checks a reviewer can perform.
- `SEEDS.txt` — exact matched-seed list.
- `SOURCE_ARCHIVE_PROVENANCE.md` — origin and checksum of the supplied archive.

## `02_source_code`

- `policies/safetypool.py` — exact unchanged SafetyPool policy source. The
  internal experiment identifier is `Karthikeya27adv8`.
- `policies/safetypool_modular.py` — same-CLI launcher for the modular form.
- `policies/safetypool_components/` — reusable policy package split by
  configuration, DQN, safety sensing, memory, experiments, metrics, plotting,
  and persistence.
- `training/train_canonical_baselines.py` — canonical baseline trainer.
- `analysis/generate_ieee_results.py` — authoritative analysis and figure
  generator for this package.
- `analysis/compare_safety_policies.py` and
  `analysis/compare_collision_policies.py` — original comparison utilities
  supplied with the experiment.
- `runners/regenerate_results.sh` — single-command package analysis.
- `runners/run_modular_policy.sh` — forwards arguments to the modular policy.
- `runners/run_seed_policy_comparison.py` — original seed-level runner.
- `tests/test_modular_policy.py` — lightweight source-parity and
  compatibility tests.

## `03_configuration`

- `experimental_protocol.json` — machine-readable evaluation design.
- `requirements.txt` and `environment.yml` — supplied Python/Conda
  environments.
- `system_specs.txt` — clean record of the original execution system.

## `04_data`

- `raw/baselines/seed_<N>/<method>/` — Epsilon-Greedy, NoisyNet, and RND
  result files for each seed.
- `raw/safetypool/seed_<N>/` — SafetyPool result files for each seed.
- `processed/` — derived tables generated from the raw result files.

The raw-data tree contains every one of the 23 matched seeds. Model weights and
training-memory snapshots are intentionally omitted because neither is needed
to recompute the reported statistics and figures.

## `05_results`

- `comparisons/aggregate/` — all-seed traces and IQM confidence-interval
  figures.
- `comparisons/seed_<N>/` — Collision RMST graph, maximum-step completion
  graph, and metric table for each seed.
- `tables/` — paper values and paired statistical tests.

Every graph is supplied as a 300-dpi PNG and a vector PDF.

## `06_checksums`

- `validation_report.json` — data/figure completeness report.
- `SHA256SUMS.txt` — integrity checksums for the delivered package contents.
