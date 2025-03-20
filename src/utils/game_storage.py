import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from core.game import Game


class GameStorage:
    def __init__(self, data_dir: str = "data/games"):
        """Initialize storage with configured data directory"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save_game(self, game_id: str, game_state: Dict[str, Any], move_metadata: Optional[Dict] = None) -> None:
        """Save game state and optional move metadata with enhanced tracking"""
        path = self.data_dir / f"{game_id}.json"

        # Load existing data if available
        if path.exists():
            with open(path) as f:
                game_data = json.load(f)
        else:
            game_data = {
                "game_id": game_id,
                "moves": [],
                "current_state": {},
                "snapshots": []
            }

        # Add current move to history with timestamp
        game_data["moves"].append({
            "move_number": len(game_data["moves"]) + 1,
            "board": game_state.move_stack[-1][0],
            "cell": game_state.move_stack[-1][1],
            "player": game_state.move_stack[-1][2],
            "timestamp": datetime.now().isoformat(),
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
            game_data = json.load(f)
            
        # Ensure snapshots field exists for backward compatibility
        if "snapshots" not in game_data:
            game_data["snapshots"] = []
            
        return game_data

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
                    'in_progress': not data['current_state']['winner'],
                    'last_updated': data['moves'][-1]['timestamp'] if data['moves'] else None
                })
        return games
        
    def restore_to_move(self, game_id: str, move_number: int) -> Optional[Dict[str, Any]]:
        """Restore game to a specific move in history without modifying the original game data"""
        game_data = self.load_game(game_id)
        if not game_data:
            print(f"Game {game_id} not found")
            return None
            
        # Validate move number
        if move_number < 0:
            print(f"Invalid move number: {move_number} (must be >= 0)")
            return None
            
        # If move_number is greater than the number of moves, use the last move
        original_move_count = len(game_data["moves"])
        if move_number > original_move_count:
            print(f"Move number {move_number} exceeds available moves {original_move_count}, using last move")
            move_number = original_move_count
            
        # If move_number is 0, return a fresh game state but keep all moves in history
        if move_number == 0:
            return {
                "game_id": game_id,
                "moves": game_data["moves"],  # Keep all moves in history
                "current_state": {
                    "board": [["" for _ in range(9)] for _ in range(9)],
                    "last_move": None,
                    "next_to_move": "x",
                    "winner": ""
                },
                "snapshots": game_data.get("snapshots", [])
            }
            
        # Create a new game state from the moves up to move_number
        from core.game import Game, make_game
        
        # Initialize an empty game
        g = Game()
        
        # Apply all moves up to the specified move number
        for i in range(move_number):
            move = game_data["moves"][i]
            g.make_move(move["board"], move["cell"], move["player"])
            
        # Validate the game state
        if not self._validate_game_state(g):
            print(f"Warning: Game state validation failed when restoring to move {move_number}")
            
        # Create a new game data object with the current state at the specified move
        # but keep all moves in the history
        restored_data = {
            "game_id": game_id,
            "moves": game_data["moves"],  # Keep all moves in history
            "current_state": {
                "board": [b.cells for b in g.board.boards],
                "last_move": g.move_stack[-1] if g.move_stack else None,
                "next_to_move": g.next_to_move,
                "winner": g.board.winner
            },
            "snapshots": game_data.get("snapshots", []),
            "current_move_index": move_number  # Add this to track where we are in the move history
        }
        
        return restored_data
        
    def _validate_game_state(self, game_state) -> bool:
        """Validate the game state for consistency"""
        try:
            # Check that board winners match cell configurations
            for i, board in enumerate(game_state.board.boards):
                expected_winner = board.evaluate_winner()
                if board.winner != expected_winner:
                    print(f"Board {i} winner mismatch: {board.winner} vs {expected_winner}")
                    return False
                    
            # Check that game winner matches board winners
            expected_game_winner = game_state.board.evaluate_winner()
            if game_state.board.winner != expected_game_winner:
                print(f"Game winner mismatch: {game_state.board.winner} vs {expected_game_winner}")
                return False
                
            return True
        except Exception as e:
            print(f"Error validating game state: {e}")
            return False
            
    def create_snapshot(self, game_id: str, label: Optional[str] = None) -> bool:
        """Create a labeled snapshot of the current game state"""
        game_data = self.load_game(game_id)
        if not game_data:
            return False
            
        # Generate snapshot ID and label
        snapshot_id = str(uuid.uuid4())
        snapshot_label = label or f"Snapshot at move {len(game_data['moves'])}"
        
        # Create snapshot entry
        snapshot = {
            "id": snapshot_id,
            "label": snapshot_label,
            "timestamp": datetime.now().isoformat(),
            "move_number": len(game_data["moves"]),
            "state": game_data["current_state"].copy()
        }
        
        # Add snapshot to game data
        if "snapshots" not in game_data:
            game_data["snapshots"] = []
        game_data["snapshots"].append(snapshot)
        
        # Save updated game data
        path = self.data_dir / f"{game_id}.json"
        temp_path = path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(game_data, f)
        temp_path.replace(path)
        
        return True
        
    def list_snapshots(self, game_id: str) -> List[Dict[str, Any]]:
        """List all snapshots for a game"""
        game_data = self.load_game(game_id)
        if not game_data or "snapshots" not in game_data:
            return []
            
        return [{
            "id": s["id"],
            "label": s["label"],
            "timestamp": s["timestamp"],
            "move_number": s["move_number"]
        } for s in game_data["snapshots"]]
        
    def restore_from_snapshot(self, game_id: str, snapshot_id: str) -> bool:
        """Restore a game from a snapshot without truncating move history"""
        game_data = self.load_game(game_id)
        if not game_data or "snapshots" not in game_data:
            return False
            
        # Find the snapshot
        snapshot = next((s for s in game_data["snapshots"] if s["id"] == snapshot_id), None)
        if not snapshot:
            return False
            
        # Create a backup of the current state
        backup_snapshot = {
            "id": str(uuid.uuid4()),
            "label": f"Auto-backup before restoring to {snapshot['label']}",
            "timestamp": datetime.now().isoformat(),
            "move_number": len(game_data["moves"]),
            "state": game_data["current_state"].copy()
        }
        
        # Update the current state from the snapshot
        game_data["current_state"] = snapshot["state"].copy()
        
        # Add current_move_index to track where we are in the move history
        # but don't truncate the move history
        game_data["current_move_index"] = snapshot["move_number"]
        
        # Add the backup to snapshots
        game_data["snapshots"].append(backup_snapshot)
        
        # Save updated game data
        path = self.data_dir / f"{game_id}.json"
        temp_path = path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(game_data, f)
        temp_path.replace(path)
        
        return True
