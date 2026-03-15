# Ultimate Tic-Tac-Toe MCTS Bot

Ultimate Tic-Tac-Toe with a Flask backend, a browser UI, persistent game storage, and a Monte Carlo Tree Search (MCTS) agent with configurable heuristics.

## Current Status

Recent revamp work on `codex-revamp` includes:
- Backend-authoritative move flow (`/api/makemove/`) to reduce state drift.
- Core state codec module for shared serialization/reconstruction logic.
- Expanded regression test suite for engine/storage/MCTS service paths.
- Reproducible benchmark harness for agent-vs-agent evaluation.
- Frontend networking decoupled via `ApiClient`.
- Full UI refresh with responsive dashboard layout.

## Requirements

- Python `>=3.10,<3.13`
- `uv` (recommended) or pip
- Modern browser

Notes:
- Python 3.10 is supported with `tomli` fallback for TOML parsing.
- Frontend is vanilla JS/CSS/HTML (no Node build step required).

## Setup

```bash
cd /home/jaden/MCTS-for-UTTT
uv venv
source .venv/bin/activate
uv sync
```

## Run Locally

Start backend:

```bash
invoke run-server --port 5000
```

Open the UI:
- `src/website/index.html`

The frontend expects the API at `http://127.0.0.1:5000` (see `src/website/js/constants.js`).

## Test Suite

Run all tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

What is currently covered:
- Core game invariants (`make_move`, `undo`, board formatting, empty-state creation)
- MCTS behavior checks (agent config propagation)
- Scoring/token normalization behavior
- Storage save/restore invariants
- Move service authority checks
- State codec serialization/replay behavior
- Benchmark reproducibility logic

Note: API tests that import Flask are auto-skipped if Flask is unavailable in the active environment.

## Benchmarking Agents

Reproducible self-play benchmark task:

```bash
invoke benchmark --agent-a default --agent-b graph_puct_v1 --games 20 --node-limit 200 --opening-random-plies 2 --seed 42
```

Equivalent CLI:

```bash
PYTHONPATH=src python -m core.benchmark \
  --agent-a default \
  --agent-b graph_puct_v1 \
  --games 20 \
  --compute-time 60 \
  --node-limit 200 \
  --opening-random-plies 2 \
  --seed 42
```

Why `node-limit` is used in benchmark mode:
- It reduces wall-clock jitter when comparing two agent versions.
- Gameplay can still use time-based thinking budgets in the UI.
- Elo tracking is tiered by node budget (`200`, `500`, `800`) with all agents starting at `1200`.
- Use `--disable-elo` when running non-tier budgets for ad-hoc experiments.

## Project Structure

```text
MCTS-for-UTTT/
├── src/
│   ├── ai/
│   │   └── mcts.py
│   ├── core/
│   │   ├── benchmark.py
│   │   ├── game.py
│   │   ├── move_service.py
│   │   ├── self_play.py
│   │   └── state_codec.py
│   ├── utils/
│   │   ├── game_score_utils.py
│   │   ├── game_storage.py
│   │   └── utils.py
│   ├── website/
│   │   ├── css/styles.css
│   │   ├── index.html
│   │   └── js/
│   │       ├── ApiClient.js
│   │       ├── ComputerPlayer.js
│   │       ├── Game.js
│   │       ├── GameState.js
│   │       └── UIManager.js
│   └── flask_server.py
├── tests/
├── docs/
└── tasks.py
```

## API Overview

- `POST /api/makemove/`
- `GET /api/games`
- `GET /api/games/{game_id}`
- `POST /api/games/rename/{game_id}`
- `POST /api/games/{game_id}/restore/{move_number}`
- `GET /api/games/{game_id}/snapshots`
- `POST /api/games/{game_id}/snapshots`
- `POST /api/games/{game_id}/snapshots/{snapshot_id}/restore`

See [API.md](docs/API.md) for endpoint payload details.

## Near-Term Roadmap

1. Improve benchmark depth and reporting (per-agent score summary, confidence intervals).
2. Add stronger API integration coverage in CI-like local workflow.
3. Begin neural-net data pipeline scaffolding (state encoder + dataset writer).
4. Integrate learned policy/value in hybrid MCTS mode.
