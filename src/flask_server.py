from flask import Flask, request, jsonify
import flask_cors
import json
import argparse

from core.game import make_game
from ai.mcts import evaluate_next_move
from utils.game_storage import GameStorage

app = Flask(__name__)
storage = GameStorage()


@app.route('/api/makemove/', methods=['POST', 'OPTIONS'])
@flask_cors.cross_origin()
def make_move():
    jsonfile = request.get_json()
    data = json.loads(jsonfile)
    game_id = data.get("game_id")

    # Create game instance from current board state after human move
    g = make_game(data["game_board"],
                  [(int(data["last_move"][0]),
                   int(data["last_move"][1]),
                   data["last_move"][2].lower())])

    # Save human move if we have a game_id
    if game_id:
        storage.save_game(game_id, g, None)  # No metadata for human moves

    # Get computer's move
    m = evaluate_next_move(g, seconds_limit=int(data["compute_time"]), verbose=False)

    # Apply computer's move and record it as the last move
    g.make_move(m[0], m[1], g.next_to_move)
    g.move_stack.append((m[0], m[1], 'o'))  # Explicitly set last_move to computer's move

    # Save after computer's move
    if game_id:
        storage.save_game(game_id, g, m[2])

    res = {"board": m[0], "cell": m[1], "metadata": m[2]}
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the UTTT Flask server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    args = parser.parse_args()

    app.run(debug=True, port=args.port)