"""
Graph PUCT core — delegates to the Rust extension for the hot search loop.
"""

import rust_mcts as _rust

DEFAULT_SECONDS_LIMIT = 30
DEFAULT_NODE_LIMIT = 100_000


def _serialize_game(game):
    boards = [[c for c in mini.cells] for mini in game.board.boards]
    mini_winners = [mini.winner for mini in game.board.boards]
    last_cell = game.move_stack[-1][1] if game.move_stack else -1
    return boards, mini_winners, game.board.winner, game.next_to_move, last_cell


def run_graph_puct(
    game,
    policy,
    budget,
    metadata=True,
    verbose=False,
):
    legal = game.legal_moves()
    if not legal:
        return None

    max_seconds = float(getattr(budget, "max_seconds", DEFAULT_SECONDS_LIMIT))
    max_nodes = int(getattr(budget, "max_nodes", DEFAULT_NODE_LIMIT))
    boards, mini_winners, global_winner, next_to_move, last_cell = _serialize_game(game)

    result = _rust.run_graph_puct(
        boards,
        mini_winners,
        global_winner,
        next_to_move,
        last_cell,
        dict(policy.config),
        max_seconds,
        max_nodes,
        metadata,
    )

    if result is None:
        return None

    if not metadata:
        return result

    if verbose and isinstance(result, list) and len(result) == 3:
        meta = result[2]
        print(f"graph_puct iterations: {meta.get('num_gamestates')}")
        print(f"graph_puct depth: {meta.get('depth_explored')}")
        print(f"graph_puct best move: ({result[0]}, {result[1]})")

    return result
