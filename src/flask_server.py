from flask import Flask, request, jsonify
import flask_cors
import json
import argparse

from core.game import make_game
from ai.mcts import evaluate_next_move
from utils.game_storage import GameStorage

app = Flask(__name__)
storage = GameStorage()


def _load_game_for_mutation(game_id):
    """Load an existing game into a mutable Game instance."""
    if not game_id:
        return None, None

    game_data = storage.load_game(game_id)
    if not game_data:
        return None, None

    current_state = game_data.get("current_state", {})
    board = current_state.get("board")
    last_move = current_state.get("last_move")
    move_stack = [tuple(last_move)] if last_move else []
    return make_game(board, move_stack), game_data


@app.route('/api/makemove/', methods=['POST', 'OPTIONS'])
@flask_cors.cross_origin()
def make_move():
    # Handle both double-encoded and single-encoded JSON
    try:
        # Try to get the data directly
        data = request.get_json()
        
        # Check if the data is a string (double-encoded JSON)
        if isinstance(data, str):
            data = json.loads(data)
    except Exception as e:
        return jsonify({"error": f"Invalid JSON format: {str(e)}"}), 400
        
    game_id = data.get("game_id")
    last_move = data.get("last_move")
    if not last_move or len(last_move) != 3:
        return jsonify({"error": "Missing or invalid last_move"}), 400

    human_board = int(last_move[0])
    human_cell = int(last_move[1])
    human_player = str(last_move[2]).lower()

    # Load existing state when possible; fallback to a new game.
    g, existing_data = _load_game_for_mutation(game_id)
    if g is None:
        # New game: trust the move intent, not client board authority.
        from core.game import Game
        g = Game()
        existing_data = None

    # Apply the human move on authoritative server state.
    if not g.make_move(human_board, human_cell, human_player):
        return jsonify({"error": "Illegal human move for current game state"}), 400

    # Save human move if we have a game_id
    if game_id:
        storage.save_game(game_id, g, None)

    # If the human move ended the game, return authoritative final state.
    if g.board.winner or not g.legal_moves():
        response = {
            "board": None,
            "cell": None,
            "metadata": None,
            "current_state": {
                "board": [b.cells for b in g.board.boards],
                "last_move": g.move_stack[-1] if g.move_stack else None,
                "next_to_move": g.next_to_move,
                "winner": g.board.winner
            },
            "move_count": len(existing_data["moves"]) + 1 if (game_id and existing_data) else len(g.move_stack)
        }
        return jsonify(response)

    # Get computer's move
    m = evaluate_next_move(g, seconds_limit=int(data["compute_time"]), verbose=False)

    # Apply computer's move
    if not g.make_move(m[0], m[1], g.next_to_move):
        return jsonify({"error": "Failed to apply computed computer move"}), 500

    # Save after computer's move
    if game_id:
        storage.save_game(game_id, g, m[2])

    prior_moves = len(existing_data["moves"]) if (game_id and existing_data) else 0
    res = {
        "board": m[0],
        "cell": m[1],
        "metadata": m[2],
        "current_state": {
            "board": [b.cells for b in g.board.boards],
            "last_move": g.move_stack[-1] if g.move_stack else None,
            "next_to_move": g.next_to_move,
            "winner": g.board.winner
        },
        "move_count": prior_moves + 2
    }
    return jsonify(res)


@app.route('/api/games', methods=['GET'])
@flask_cors.cross_origin()
def list_games():
    # Only show in-progress games by default
    in_progress = request.args.get('in_progress', 'true').lower() == 'true'
    games = storage.list_games(in_progress_only=in_progress)
    return jsonify(games)


@app.route('/api/games/<game_id>', methods=['GET'])
@flask_cors.cross_origin()
def get_game(game_id):
    game_data = storage.load_game(game_id)
    if game_data:
        return jsonify(game_data)
    return jsonify({"error": "Game not found"}), 404


@app.route('/api/games/rename/<game_id>', methods=['POST', 'OPTIONS'])
@flask_cors.cross_origin()
def rename_game(game_id):
    try:
        data = request.get_json()
        new_name = data.get('name')
        print(f"Renaming game {game_id} to {new_name}")  # Debug log
        if not new_name:
            return jsonify({"error": "Name is required"}), 400
        success = storage.rename_game(game_id, new_name)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Game not found"}), 404

    except Exception as e:
        print(f"Error renaming game: {e}")
        return jsonify({"error": "Server error"}), 500


@app.route('/api/games/<game_id>/restore/<int:move_number>', methods=['POST'])
@flask_cors.cross_origin()
def restore_to_move(game_id, move_number):
    """Restore a game to a specific move in its history without modifying the original game data"""
    try:
        restored_data = storage.restore_to_move(game_id, move_number)
        if restored_data:
            # Don't save the restored state to disk, just return it to the client
            return jsonify({"success": True, "game": restored_data})
        else:
            return jsonify({"error": "Failed to restore game"}), 400
    except Exception as e:
        print(f"Error restoring game to move {move_number}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/games/<game_id>/snapshots', methods=['GET'])
@flask_cors.cross_origin()
def list_snapshots(game_id):
    """List all snapshots for a game"""
    try:
        snapshots = storage.list_snapshots(game_id)
        return jsonify(snapshots)
    except Exception as e:
        print(f"Error listing snapshots: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/games/<game_id>/snapshots', methods=['POST'])
@flask_cors.cross_origin()
def create_snapshot(game_id):
    """Create a new snapshot of the current game state"""
    try:
        data = request.get_json() or {}
        label = data.get('label')
        success = storage.create_snapshot(game_id, label)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Failed to create snapshot"}), 400
    except Exception as e:
        print(f"Error creating snapshot: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/games/<game_id>/snapshots/<snapshot_id>/restore', methods=['POST'])
@flask_cors.cross_origin()
def restore_snapshot(game_id, snapshot_id):
    """Restore a game from a specific snapshot"""
    try:
        success = storage.restore_from_snapshot(game_id, snapshot_id)
        if success:
            # Reload the game data after restoration
            game_data = storage.load_game(game_id)
            return jsonify({"success": True, "game": game_data})
        else:
            return jsonify({"error": "Failed to restore snapshot"}), 400
    except Exception as e:
        print(f"Error restoring snapshot: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the UTTT Flask server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    args = parser.parse_args()

    app.run(debug=True, port=args.port)
