from core.game import Game, make_game


def serialize_current_state(game):
    return {
        "board": [b.cells for b in game.board.boards],
        "last_move": game.move_stack[-1] if game.move_stack else None,
        "next_to_move": game.next_to_move,
        "winner": game.board.winner,
    }


def _load_existing_game(storage, game_id):
    if not game_id:
        return None, 0

    game_data = storage.load_game(game_id)
    if not game_data:
        return None, 0

    current_state = game_data.get("current_state", {})
    board = current_state.get("board")
    last_move = current_state.get("last_move")
    move_stack = [tuple(last_move)] if last_move else []
    game = make_game(board, move_stack)
    prior_moves = len(game_data.get("moves", []))
    return game, prior_moves


def apply_human_and_ai_move(storage, game_id, human_move, compute_time, evaluate_fn):
    """Apply a human move then (if game is still live) apply AI response.

    Raises:
        ValueError: Illegal client input or illegal move.
        RuntimeError: AI computation/application failures.
    """
    if not human_move or len(human_move) != 3:
        raise ValueError("Missing or invalid last_move")

    human_board = int(human_move[0])
    human_cell = int(human_move[1])
    human_player = str(human_move[2]).lower()

    game, prior_moves = _load_existing_game(storage, game_id)
    if game is None:
        game = Game()
        prior_moves = 0

    if not game.make_move(human_board, human_cell, human_player):
        raise ValueError("Illegal human move for current game state")

    if game_id:
        storage.save_game(game_id, game, None)

    if game.board.winner or not game.legal_moves():
        return {
            "board": None,
            "cell": None,
            "metadata": None,
            "current_state": serialize_current_state(game),
            "move_count": prior_moves + 1,
        }

    ai_result = evaluate_fn(game, seconds_limit=int(compute_time), verbose=False)
    if not ai_result or len(ai_result) < 3:
        raise RuntimeError("AI move evaluation returned invalid result")

    ai_board, ai_cell, ai_metadata = ai_result
    if not game.make_move(ai_board, ai_cell, game.next_to_move):
        raise RuntimeError("Failed to apply computed computer move")

    if game_id:
        storage.save_game(game_id, game, ai_metadata)

    return {
        "board": ai_board,
        "cell": ai_cell,
        "metadata": ai_metadata,
        "current_state": serialize_current_state(game),
        "move_count": prior_moves + 2,
    }
