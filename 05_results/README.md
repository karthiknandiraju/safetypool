# Results

The results tree is generated entirely from `04_data/raw/`. All graphs are
grouped under `comparisons/`, with a separate directory for every seed.

- `comparisons/aggregate/` provides two views of each confirmatory metric:
  - all 23 matched seed values;
  - the interquartile mean with a 95% seed-bootstrap interval.
- `comparisons/seed_<N>/` contains a metric CSV and a four-method graph for
  Collision RMST and maximum-step completion.
- `tables/` contains the paper/recomputed RMST table and all paired
  Wilcoxon/Holm tests.

Each figure is delivered as a 300-dpi PNG for convenient manuscript use and a
vector PDF for publication-quality scaling.
