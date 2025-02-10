# Ultimate Tic-Tac-Toe Backend

## Overview
The backend implements an Ultimate Tic-Tac-Toe game with Monte Carlo Tree Search (MCTS) AI. The system is structured as a Python package with distinct modules for game logic, AI strategy, and utilities.

## Project Structure
```
/src
├── core/
│   ├── game.py        # Core game mechanics and state management
├── ai/
│   ├── mcts.py        # MCTS implementation for AI moves
├── utils/
│   ├── board_utils.py # Board analysis and scoring functions
├── config.py          # Configuration and parameters
└── server.py          # Flask server for API endpoints
```

## Key Components

### Game Logic (core/game.py)
Contains three main classes:
- `MiniBoard`: Represents a single tic-tac-toe board
- `Board`: Manages 9 MiniBoards for the full game
- `Game`: Coordinates game flow and move validation

### AI Strategy (ai/mcts.py)
Implements Monte Carlo Tree Search with:
- `SimulationTreeNode`: Represents a node in the MCTS tree
- `evaluate_next_move`: Main function for computing AI moves
- Configurable parameters for search depth and timing

### Board Utilities (utils/board_utils.py)
Helper functions for board analysis:
- `three_in_a_row`: Checks for winning conditions
- `game_value`: Evaluates board positions using Russell/Norvig scoring

### Configuration (config.py)
Contains parameters for:
- MCTS search configuration
- Time thresholds for move computation
- Early stopping conditions
- Position complexity thresholds

### API Server (server.py)
Flask server providing:
- POST /api/makemove/: Endpoint for requesting AI moves
- Cross-origin support for frontend integration

## Key Features
1. Full Ultimate Tic-Tac-Toe rule implementation
2. MCTS-based AI with configurable search parameters
3. Position evaluation using classic game theory metrics
4. RESTful API for frontend integration
5. Early stopping optimization for move computation

## Game Flow
1. Frontend sends current game state to /api/makemove/
2. Backend constructs Game instance from state
3. MCTS algorithm computes next move
4. Response includes move coordinates and computation metadata

## Scoring System
The game uses a sophisticated scoring mechanism that considers:
- Immediate wins/losses (highest priority)
- Potential winning lines
- Board control and positioning
- Both local (mini-board) and global (full board) state

## MCTS Implementation
The AI uses MCTS with:
- UCB1 for node selection
- Adaptive computation based on position complexity
- Early stopping when confident about best move
- Metadata collection for move analysis