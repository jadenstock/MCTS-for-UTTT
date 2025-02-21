import json
from pathlib import Path
from typing import Optional, Dict, Any


class GameStorage:
    def __init__(self, data_dir: str = "data/games"):
        """Initialize storage with configured data directory"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save_game(self, game_id: str, game_state: Dict[str, Any], move_metadata: Optional[Dict] = None) -> None:
        """Save game state and optional move metadata"""
        path = self.data_dir / f"{game_id}.json"

        # Load existing data if available
        if path.exists():
            with open(path) as f:
                game_data = json.load(f)
        else:
            game_data = {
                "game_id": game_id,
                "moves": [],
                "current_state": {}
            }

        # Add current move to history
        game_data["moves"].append({
            "move_number": len(game_data["moves"]) + 1,
            "board": game_state.move_stack[-1][0],
            "cell": game_state.move_stack[-1][1],
            "player": game_state.move_stack[-1][2],
            "metadata": move_metadata if move_metadata else None
        })

        # Update current state
        game_data["current_state"] = {
            "board": [b.cells for b in game_state.board.boards],
            "last_move": game_state.move_stack[-1],
            "next_to_move": game_state.next_to_move,
            "winner": game_state.board.winner
        }

        # Atomic write
        temp_path = path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(game_data, f)
        temp_path.replace(path)

    def rename_game(self, game_id: str, new_name: str) -> bool:
        """Create a new save file with new game_id"""
        old_path = self.data_dir / f"{game_id}.json"
        if not old_path.exists():
            return False

        try:
            with open(old_path) as f:
                game_data = json.load(f)

            # Create new save with new game_id and same content
            game_data["game_id"] = new_name  # Use the new name as the game_id

            # Save to new file
            new_path = self.data_dir / f"{new_name}.json"
            temp_path = new_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(game_data, f)
            temp_path.replace(new_path)
            return True
        except Exception as e:
            print(f"Error creating new save file: {e}")
            return False

    def load_game(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Load game data by ID"""
        path = self.data_dir / f"{game_id}.json"
        if not path.exists():
            return None

        with open(path) as f:
            return json.load(f)

    def list_games(self, in_progress_only: bool = False) -> list:
        """List saved games with optional filtering for in-progress games only"""
        games = []
        for path in self.data_dir.glob('*.json'):
            with open(path) as f:
                data = json.load(f)
                # Skip completed games if filtering
                if in_progress_only and data['current_state']['winner']:
                    continue

                games.append({
                    'game_id': data['game_id'],
                    'moves': len(data['moves']),
                    'winner': data['current_state']['winner'],
                    'next_to_move': data['current_state']['next_to_move'],
                    'in_progress': not data['current_state']['winner']
                })
        return games