"""
MCTS core — delegates to the Rust extension for the hot search loop.
The public API (run_mcts, SimulationTreeNode, DEFAULT_*) is unchanged so
all existing callers continue to work without modification.
"""

import rust_mcts as _rust

DEFAULT_SECONDS_LIMIT = 30
DEFAULT_NODE_LIMIT = 100_000


def _serialize_game(game):
    boards = [[c for c in mini.cells] for mini in game.board.boards]
    mini_winners = [mini.winner for mini in game.board.boards]
    last_cell = game.move_stack[-1][1] if game.move_stack else -1
    return boards, mini_winners, game.board.winner, game.next_to_move, last_cell


def _policy_type_str(policy):
    name = type(policy).__name__
    if "Pragmatic" in name:
        return "pragmatic"
    # GraphPUCT bots that fall through to run_mcts (shouldn't normally happen)
    return "baseline"


def run_mcts(
    game,
    policy,
    budget,
    agent_id="default",
    metadata=True,
    verbose=False,
):
    legal = game.legal_moves()
    if not legal:
        return None

    max_seconds = float(getattr(budget, "max_seconds", DEFAULT_SECONDS_LIMIT))
    max_nodes = int(getattr(budget, "max_nodes", DEFAULT_NODE_LIMIT))
    boards, mini_winners, global_winner, next_to_move, last_cell = _serialize_game(game)

    result = _rust.run_mcts(
        boards,
        mini_winners,
        global_winner,
        next_to_move,
        last_cell,
        dict(policy.config),
        _policy_type_str(policy),
        max_seconds,
        max_nodes,
        metadata,
    )

    if result is None:
        return None

    if not metadata:
        # Rust returns a tuple (board_idx, cell_idx)
        return result

    if verbose and isinstance(result, list) and len(result) == 3:
        meta = result[2]
        print(f"number of gamestates evaluated: {meta.get('num_gamestates')}")
        print(f"depth of game tree explored: {meta.get('depth_explored')}")
        print(f"best move for {next_to_move}: ({result[0]}, {result[1]})")
        moves = meta.get("moves", [])
        if moves:
            best = moves[0]
            print(f"score of best move: {best[1]}")
        print("top moves:")
        for mv, score, plays in moves:
            print(f"\tmove: {mv}\tnum_plays: {plays}\tscore: {score}")

    return result


# ---------------------------------------------------------------------------
# Compatibility shim — SimulationTreeNode is used in a handful of tests.
# It wraps the Rust search so existing test assertions still work.
# ---------------------------------------------------------------------------

class SimulationTreeNode:
    """Thin wrapper kept for backward compatibility with tests."""

    def __init__(self, game, player, agent_id="default"):
        from bots.registry import get_bot
        bot = get_bot(agent_id)
        self._game = game
        self._player = player
        self._policy = bot.policy
        self._agent_id = agent_id
        # Minimal attributes tests may inspect
        self.number_of_plays = 0
        self.total_score = 0.0
        self.children = {}

    def expand_tree_by_one(self):
        """Run a single MCTS iteration (delegates to Rust)."""
        from bots.base import SearchBudget
        budget = SearchBudget(max_seconds=0.0, max_nodes=1)
        result = run_mcts(
            self._game,
            self._policy,
            budget,
            agent_id=self._agent_id,
            metadata=False,
        )
        if result:
            self.number_of_plays += 1

    def get_score_of_move(self, move):
        child = self.children.get(move)
        if child is None:
            return None
        return child.total_score / child.number_of_plays
