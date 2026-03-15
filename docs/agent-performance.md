# Agent Performance Log

This document tracks observed performance, hypotheses, and next experiments for each bot.

## Evaluation Protocol

- Primary budget: `node_limit`
- Secondary safety cap: `compute_time` (seconds)
- Match format: alternating sides each game
- Opening diversity: random opening plies (`opening_random_plies`)
- Persist all games to `data/benchmark_games` for replay analysis

## Current Agents

- `default` (baseline MCTS)
- `pragmatic_v1` (tactical/heuristic revision)
- `graph_puct_v1` (PUCT + transposition-table graph search)

## Results Snapshot (2026-03-14)

### Batch A
- Command profile: `games=8`, `compute_time=1`, `node_limit=40`, `opening_random_plies=1`
- Summary:
  - `pragmatic_v1`: 3 wins
  - `default`: 2 wins
  - draws: 3
- Side split:
  - `pragmatic_v1` as X: 1W / 2D / 1L
  - `pragmatic_v1` as O: 2W / 1D / 1L

### Batch B
- Command profile: `games=3`, `compute_time=2`, `node_limit=120`, `opening_random_plies=1`
- Summary:
  - `pragmatic_v1`: 1 win
  - `default`: 2 wins
  - draws: 0

## Working Hypotheses

- `pragmatic_v1` tactical biases are useful in some positions but may overfit local patterns.
- `default` appears more stable as budgets increase in this small sample.
- More games are required before promoting a champion.

## Next Experiments

1. Run 30-game sets at fixed node budgets: `80`, `200`, `500`.
2. Compare side-adjusted win rate (X/O split), not only total wins.
3. Tag losses by blunder class (missed block, failed board conversion, send-to-losing board).
4. Add Elo tracking over all persisted benchmark games.

## New Family Notes (2026-03-14)

- `graph_puct_v1` introduces two algorithmic changes:
  - PUCT selection with heuristic move priors.
  - Transposition-table graph search that reuses stats across repeated states.
- Smoke run (`games=4`, `compute_time=1`, `node_limit=80`, `opening_random_plies=1`) vs `default`:
  - `graph_puct_v1`: 3 wins
  - `default`: 1 win
  - draws: 0
