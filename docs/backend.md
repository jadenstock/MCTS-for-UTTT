# Ultimate Tic-Tac-Toe Backend Documentation

## Architecture Overview

The Ultimate Tic-Tac-Toe backend implements a sophisticated game engine with Monte Carlo Tree Search (MCTS) AI and persistent game storage. The system is built in Python with a Flask-based API server.

## Project Structure

```
/src
├── core/
│   ├── game.py           # Core game logic and state management
│   └── game_storage.py   # Game persistence and data management
├── ai/
│   └── mcts.py          # Monte Carlo Tree Search implementation
├── utils/
│   └── board_utils.py   # Board evaluation utilities
├── config.py            # System configuration and constants
└── server.py           # Flask API server
```

## Core Components

### Game Engine (game.py)

The game engine uses a hierarchical structure:

#### MiniBoard Class
```python
class MiniBoard:
    cells: List[str]       # 9 cells for single board
    winner: str           # Current winner ("", "x", "o")
    
    def legal_cells() -> List[int]
    def score(player: str) -> float
    def evaluate_winner() -> str
```

#### Board Class
```python
class Board:
    boards: List[MiniBoard]  # 9 mini-boards
    winner: str            # Overall winner
    
    def score(player: str) -> float
    def evaluate_winner() -> str
```

#### Game Class
```python
class Game:
    board: Board
    last_move: Tuple[int, int, str]  # (board, cell, player)
    next_to_move: str
    
    def legal_moves() -> List[Tuple[int, int]]
    def make_move(board: int, cell: int, player: str)
    def greedy_next_move() -> Tuple[int, int]
```

### AI System (mcts.py)

#### SimulationTreeNode Class
```python
class SimulationTreeNode:
    game: Game
    player: str
    number_of_plays: int
    children: Dict[Tuple[int, int], SimulationTreeNode]
    total_score: float
    depth_seen: int
    unseen_children: List[Tuple[int, int]]
    best_move_stable_count: int
```

Key Methods:
- `get_score_of_move(move)`: Calculates average score for a move
- `get_best_action_by_average_score()`: Selects best move by average score
- `get_best_action_and_confidence()`: Returns best move with confidence metric
- `expand_tree_by_one()`: Expands search tree by one node

#### MCTS Configuration
```python
COMPUTE_TIME_THRESHOLDS = {
    'GREEDY': 5,      # Use greedy strategy below this
    'MEDIUM': 15      # Affects computation distribution
}

POSITION_THRESHOLDS = {
    'COMPLEX': 20,    # Many legal moves
    'MEDIUM': 10      # Moderate number of moves
}

EARLY_STOPPING = {
    'CONFIDENCE_HIGH': 0.8,
    'CONFIDENCE_MODERATE': 0.6,
    'STABLE_CHECKS_HIGH': 5,
    'STABLE_CHECKS_MODERATE': 10
}
```

### Game Storage (game_storage.py)

#### GameStorage Class
```python
class GameStorage:
    data_dir: Path
    
    def save_game(game_id: str, game_state: Dict, metadata: Dict)
    def load_game(game_id: str) -> Dict
    def list_games(in_progress_only: bool = False) -> List[Dict]
```

Game State Format:
```json
{
    "game_id": string,
    "moves": [
        {
            "move_number": int,
            "board": int,
            "cell": int,
            "player": string,
            "metadata": object
        }
    ],
    "current_state": {
        "board": [[string]],
        "last_move": [int, int, string],
        "next_to_move": string,
        "winner": string
    }
}
```

### Board Utilities (board_utils.py)

Key Functions:
```python
def three_in_a_row(board: List[str]) -> str
def game_value(board: List[str], player: str) -> float
```

Scoring System:
- Uses Russell/Norvig evaluation function
- Considers line completion potential
- Weights two-in-a-row formations
- Normalizes scores to [0,1] range

## API Endpoints

### POST /api/makemove/
Request:
```json
{
    "game_id": string,
    "last_move": [int, int, string],
    "game_board": [[string]],
    "compute_time": int,
    "force_full_time": boolean
}
```

Response:
```json
{
    "board": int,
    "cell": int,
    "metadata": {
        "num_gamestates": int,
        "depth_explored": int,
        "thinking_time": float,
        "moves": [[int, int, float]],
        "early_stop": boolean
    }
}
```

### GET /api/games
Response:
```json
[{
    "game_id": string,
    "moves": int,
    "winner": string,
    "next_to_move": string,
    "in_progress": boolean
}]
```

### GET /api/games/{game_id}
Response: Full game state object

## AI Strategy

### Move Selection Process
1. Initialize MCTS root node with current game state
2. Expand tree within time/node limits:
   - Use UCB1 for node selection
   - Expand unexplored nodes first
   - Update scores through tree
3. Select best move based on average scores
4. Apply early stopping if confident

### Early Stopping Conditions
- High confidence (>0.8) and stable for 5 checks
- Moderate confidence (>0.6) and stable for 10 checks
- Any move stable for 15 checks

### Computation Distribution
Based on:
- Available computation time
- Position complexity (legal moves count)
- Game progression stage

## Game Logic Details

### Move Validation
1. Check move legality:
   - Correct player
   - Empty cell
   - Valid target board
2. Special cases:
   - First move (any board)
   - Target board won/full (any board)

### Board Evaluation
- Immediate wins/losses (±1.0)
- Potential winning lines (±0.2 per line)
- Board control (±0.1 per controlled area)
- Normalized to [0,1] range

## Performance Considerations

### Memory Management
- Copy-on-write for game states
- Garbage collection after expansive searches
- Atomic file writes for game storage

### Computation Optimization
- Early stopping for confident positions
- Adaptive search depth based on position
- Greedy fallback for time-constrained moves

## Future Improvements

1. Performance
   - Parallelized tree search
   - Position hash table
   - Move ordering optimization

2. Features
   - Opening book integration
   - Position analysis cache
   - Move explanation system

3. Analysis
   - Move strength evaluation
   - Position complexity metrics
   - Learning from game history