from core.game import Game, make_game


def serialize_game_state(game):
    return {
        "board": [b.cells for b in game.board.boards],
        "last_move": game.move_stack[-1] if game.move_stack else None,
        "next_to_move": game.next_to_move,
        "winner": game.board.winner,
    }


def game_from_current_state(current_state):
    board = current_state.get("board", [["" for _ in range(9)] for _ in range(9)])
    last_move = current_state.get("last_move")
    move_stack = [tuple(last_move)] if last_move else []
    return make_game(board, move_stack)


def replay_game_from_moves(moves):
    game = Game()
    for move in moves:
        game.make_move(move["board"], move["cell"], move["player"])
    return game
