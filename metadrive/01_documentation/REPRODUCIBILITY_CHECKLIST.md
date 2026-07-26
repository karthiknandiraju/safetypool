# Reproducibility Checklist

Use this checklist after extracting the archive.

- [ ] Read `00_README_FIRST.md`.
- [ ] Confirm Python 3.11 and install `03_configuration/requirements.txt`.
- [ ] Run `bash 02_source_code/runners/regenerate_results.sh`.
- [ ] Confirm the command prints `PASS: validated 23 seeds x 4 methods`.
- [ ] Confirm `04_data/processed/data_completeness.csv` contains 92 `PASS`
      records.
- [ ] Confirm `05_results/comparisons/` contains 23 seed directories and one
      `aggregate` directory.
- [ ] Confirm each seed directory has both Collision RMST and maximum-step
      completion figures in PNG and PDF.
- [ ] Confirm `05_results/comparisons/aggregate/` contains all-seed and IQM
      figures for both metrics.
- [ ] Confirm all six Holm-adjusted comparisons in
      `05_results/tables/paired_statistical_tests.csv` are below 0.05.
- [ ] Run `sha256sum -c 06_checksums/SHA256SUMS.txt` from the package root.

The delivered figures are generated outputs. Re-running the analysis is
expected to reproduce the metric tables exactly. PDF metadata and byte-level
image compression can vary across Matplotlib versions even when the displayed
figure is unchanged.
