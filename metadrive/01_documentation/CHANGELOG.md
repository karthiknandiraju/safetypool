# Artifact Changelog

## Modular-policy revision

- Preserved `02_source_code/policies/safetypool.py` byte-for-byte.
- Added `02_source_code/policies/safetypool_modular.py` as a compatible
  command-line launcher.
- Added the commented `safetypool_components/` package, separating constants,
  utilities, safety sensing, environment integration, DQN learning,
  safety-memory responsibilities, action selection, experiment loops, metrics,
  plotting, persistence, and CLI orchestration.
- Split the original 3,900-line safety-memory class into eight focused mixins
  while retaining all 97 method bodies.
- Added architecture and extension documentation.
- Added seven lightweight compatibility tests, including AST parity and a
  live candidate/invariant check for the composed memory.
- Added `runners/run_modular_policy.sh`.

Raw experiment data, comparison metrics, statistical results, and figures were
not altered by the source-code modularization.
