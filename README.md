# Reward-Guided Exploration in HighwayEnv: Epsilon Greedy vs Median 50

This project compares **Epsilon Greedy** and **Median 50** exploration for autonomous highway driving. Both experiments use the same HighwayEnv scenario, DQN architecture, reward configuration, intrinsic-reward components, hyperparameters, episode seeds, and evaluation procedure. Each strategy trains an independent network, target network, replay buffer, optimizer, and intrinsic-reward state.

The analysis and plotting script are deliberately restricted to these two strategies. Rows belonging to any other experiment in the CSV are ignored and cannot appear in the figures or calculated statistics.

## Video

https://youtu.be/EQdsNJjQBuQ

## Research objective

The experiment tests whether directing exploratory actions toward the lower half of the current action-value distribution changes convergence, reward, stability, and driving performance relative to uniformly random exploration.

The analysis covers:

- training reward convergence;
- the episode and measured time at 95% convergence;
- overall testing reward distributions;
- testing reward distributions in 100-episode blocks;
- overall and block-wise training reward distributions;
- training reward variability;
- testing collision and error frequencies; and
- steps completed before collision.

## Highway driving environment

The experiment uses `highway-v0` with:

| Setting | Value |
|---|---:|
| Lanes | 4 |
| Traffic vehicles | 40 |
| Observed vehicles | 5 |
| Maximum episode steps | 500 |
| Simulation frequency | 15 Hz |
| Policy frequency | 5 Hz |

The kinematics observation records presence, relative position, and velocity information for the ego vehicle and nearby vehicles. It is flattened before being passed to the DQN.

The discrete driving actions are the HighwayEnv meta-actions for changing lanes, maintaining behaviour, accelerating, and decelerating.

## Reward design

The environment reward uses the same settings for both strategies:

| Reward parameter | Value |
|---|---:|
| Collision reward | −1.0 |
| Right-lane reward | 0.1 |
| High-speed reward | 0.4 |
| Lane-change reward | 0.0 |
| Reward speed range | 20–30 |
| Reward normalization | Enabled |

During training, the environment reward is augmented by Random Network Distillation and count-based intrinsic rewards. The stored `env_reward` is used for the primary performance and convergence graphs so that both strategies are compared using the external driving objective. During testing, intrinsic bonuses are disabled and only environment reward is recorded.

## Shared DQN configuration

| Parameter | Value |
|---|---:|
| Training episodes | 500 |
| Testing episodes | 300 |
| Maximum steps per episode | 500 |
| Epsilon | 0.20 |
| Learning rate | 0.00005 |
| Discount factor | 0.99 |
| Batch size | 64 |
| Replay capacity | 50,000 |
| Target-network update interval | 1,000 learning steps |
| Hidden-layer size | 128 |
| RND coefficient | 0.01 |
| Count coefficient | 0.05 |
| Random seed | 42 |

The DQN uses two hidden layers with ReLU activations, an Adam optimizer, replay sampling, a target network, and Smooth L1 loss.

## Exploration strategies

### Epsilon Greedy

At every training step:

- with probability `0.2`, choose uniformly from all available actions;
- with probability `0.8`, choose an action with the maximum predicted Q-value.

Exploration is sampled independently at each step and continues throughout all training episodes.

### Median 50

At every training step:

- with probability `0.2`, calculate the median Q-value and randomly choose from actions whose Q-values are less than or equal to the median;
- with probability `0.8`, choose an action with the maximum predicted Q-value.

Median 50 therefore uses the same exploration frequency as Epsilon Greedy but restricts exploratory selection to the lower half of the predicted action-value distribution. Both strategies use random tie-breaking among equally valued greedy actions.

## Frozen testing

Testing uses 300 episodes per strategy. The trained networks are frozen, action selection is greedy, and there are no optimizer, replay-buffer, target-network, RND, count, or network updates. Both strategies use the same test-seed schedule.

## Recorded results

| Testing metric | Epsilon Greedy | Median 50 |
|---|---:|---:|
| Mean environment reward | 31.07 | 33.98 |
| Median environment reward | 25.85 | 28.93 |
| Reward standard deviation | 21.45 | 23.81 |
| Mean steps before collision | 32.36 | 35.31 |
| Median steps before collision | 27 | 30 |
| Collision outcomes | 300 of 300 | 300 of 300 |
| Error outcomes | 0 | 0 |

Median 50 produced higher mean and median testing reward and completed slightly more steps before collision. However, it did **not** reduce testing collision frequency: every test episode for both strategies ended in collision. The figures report this result directly and do not claim a collision reduction.

Using the 95% criterion described below, both strategies first reached the threshold at training episode 10. The measured cumulative time through episode 10 was 94.85 seconds for Epsilon Greedy and 78.97 seconds for Median 50.

## Generate the graphs

Place `plot.py` in the Highway project's `src` directory:

```text
highway/
├── src/
│   ├── highway.py
│   └── plot.py
└── results/
    ├── all_episode_results.csv
    └── plots/
```

Install the plotting dependencies if needed:

```bash
python3 -m pip install pandas numpy matplotlib pillow
```

From the project root, run:

```bash
python3 src/plot.py
```

For a differently named results directory:

```bash
python3 src/plot.py --results-dir /absolute/path/to/results
```

The script reads `all_episode_results.csv` and writes the following files to `results/plots`:

| No. | JPEG figure |
|---:|---|
| 01 | Training reward convergence |
| 02 | 95% convergence episode |
| 03 | Measured cumulative time to 95% convergence |
| 04 | Overall testing reward box plot |
| 05 | Testing reward box plots for episodes `1–100`, `101–200`, and `201–300` |
| 06 | Overall training reward box plot |
| 07 | Training reward box plots in 100-episode blocks |
| 08 | Training reward variability by 100-episode block |
| 09 | Full testing collision and error frequency; max-step information is omitted |
| 10 | Testing steps-before-collision box plot |

## Convergence definition

For each strategy, the script calculates a 10-episode rolling mean of training environment reward:

```text
95% threshold = 0.95 × mean frozen-test environment reward
```

The convergence episode is the first episode at which the rolling training mean reaches or exceeds the threshold. Convergence time is the sum of the recorded training episode wall times through that episode.
