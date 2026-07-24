# Modular SafetyPool Architecture

## Purpose

The original `policies/safetypool.py` is 7,927 lines. It is preserved unchanged
as the archival implementation that generated the supplied experiments. A
second implementation under `policies/safetypool_components/` separates the
same behavior into reusable, documented components.

## Component map

| Component | Responsibility |
|---|---|
| `constants.py` | Shared policy names, schemas, and configuration-key contracts |
| `utils.py` | Determinism, hashing, serialization, arrays, and RMST |
| `safety.py` | Safety-vector extraction, normalization, and threshold calibration |
| `environment.py` | Lazy MetaDrive creation and termination parsing |
| `dqn.py` | Q-network, transition model, replay buffer, and DQN agent |
| `memory/record.py` | Unified candidate/active/retired/hazard record |
| `memory/storage.py` | Storage slots, status indexes, masks, evidence, and invariants |
| `memory/matching.py` | Strict and capacity-fallback vectorized matching |
| `memory/capacity.py` | Permanent capacity, promotion, and retirement transitions |
| `memory/outcomes.py` | Immediate, delayed, warning, and interrupted outcomes |
| `memory/candidates.py` | Candidate absorption, hazard archiving, and eviction |
| `memory/state_processing.py` | Centroids, matched-state updates, and candidate reception |
| `memory/selection.py` | Candidate, active, retired, and hazard action selection |
| `memory/diagnostics.py` | Pool and matching statistics |
| `memory/pools.py` | Public memory class composed from the eight focused mixins |
| `action_selection.py` | Training action routing between DQN and SafetyPool |
| `experiment.py` | Training, frozen evaluation, and episode-row construction |
| `metrics.py` | Collision RMST and safety-stop summaries |
| `plotting.py` | General IEEE-styled figures |
| `pool_reporting.py` | Pool CSV diagnostics and figures |
| `persistence.py` | Canonical outputs, models, manifests, and indexes |
| `configuration.py` | Parser construction, validation, and output paths |
| `cli.py` | Thin application orchestration |

## Dependency flow

```text
configuration ─┐
constants ─────┼─> cli ─> experiment ─> action_selection
utils ─────────┤                   │              │
environment ───┤                   │              ├─> dqn
persistence ───┘                   │              └─> memory
                                  └─> safety

memory = storage + matching + capacity + outcomes + candidates
       + state processing + selection + diagnostics
```

Dependencies point toward focused domain services. The memory mixins
communicate through the public state of `SimilarStateActionPools`; external
callers continue to use one stable class.

## DRY and SOLID choices

- **DRY:** policy names, CSV schemas, critical configuration keys, and shared
  utilities have one definition.
- **Single Responsibility:** learning, safety sensing, memory, action
  selection, experiment execution, metrics, plotting, persistence, and CLI
  concerns are separate.
- **Open/Closed:** matching, outcomes, candidate lifecycle, or selection
  behavior can be extended in its focused mixin without editing the DQN or
  reporting layers.
- **Liskov Substitution:** the composed `SimilarStateActionPools` retains the
  original public methods and state behavior.
- **Interface Segregation:** modules import only the services required for
  their responsibility.
- **Dependency Inversion:** the orchestration layer coordinates domain
  services; MetaDrive is imported only when an environment is created.

## Compatibility

Run the modular implementation with the same arguments:

```bash
python -u policies/safetypool_modular.py --help
```

or, from `02_source_code/`:

```bash
python -m policies.safetypool_components --help
```

The policy identifier remains `Karthikeya27adv8`; therefore existing comparison
scripts and output discovery continue to work.

## Verification

`tests/test_modular_policy.py` checks:

1. the archived monolith has not changed;
2. every new Python file has a module-level explanation;
3. all 97 original safety-memory methods are present exactly once across eight
   focused mixins;
4. every non-adapter function/class body is AST-equivalent to the monolith;
5. parser defaults still specify 500 training episodes, 300 test episodes,
   and a 500-step horizon; and
6. memory mixins remain separated by responsibility.
7. the composed memory can create a candidate and pass its original invariant
   checks.

Run:

```bash
python -m unittest discover -s tests -v
```

The lightweight tests require Python and NumPy but do not create MetaDrive
environments, load PyTorch, or train a model. Full experiment execution
requires the supplied environment dependencies and CUDA when `--device cuda`
is selected.
