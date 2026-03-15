import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bots.base import SearchBudget
from bots.registry import get_bot, list_bot_ids
from core.game import make_game


class TestGraphPUCTBot(unittest.TestCase):
    def test_graph_puct_bot_is_registered(self):
        self.assertIn("graph_puct_v1", list_bot_ids())

    def test_graph_puct_takes_immediate_global_win(self):
        board = [["" for _ in range(9)] for _ in range(9)]
        board[0] = ["o", "o", "", "", "", "", "", "", ""]
        board[1] = ["o", "o", "o", "", "", "", "", "", ""]
        board[2] = ["o", "o", "o", "", "", "", "", "", ""]
        board[4][0] = "x"

        game = make_game(board, [(4, 0, "x")])
        bot = get_bot("graph_puct_v1")
        result = bot.choose_move(game, SearchBudget(max_seconds=5, max_nodes=120), metadata=False, verbose=False)
        self.assertEqual(result, (0, 2))

    def test_graph_puct_visits_each_root_move_with_enough_budget(self):
        board = [["" for _ in range(9)] for _ in range(9)]
        game = make_game(board, [(0, 5, "x")])
        bot = get_bot("graph_puct_v1")
        result = bot.choose_move(game, SearchBudget(max_seconds=2, max_nodes=9), metadata=True, verbose=False)
        self.assertIsNotNone(result)
        metadata = result[2]
        # With 9 legal moves and a 9-node budget, each root move should be sampled once.
        rollouts = [int(m[2]) for m in metadata["moves"]]
        self.assertEqual(len(rollouts), 9)
        self.assertTrue(all(r >= 1 for r in rollouts))

    def test_graph_puct_uses_exact_endgame_solver_under_threshold(self):
        draw_board = ["x", "o", "x", "x", "o", "o", "o", "x", "x"]
        x_won_board = ["x", "x", "x", "o", "o", "x", "o", "x", "o"]
        board = [list(draw_board) for _ in range(9)]
        board[0] = ["", "", "x", "x", "o", "o", "o", "x", "x"]
        board[4] = list(x_won_board)
        board[8] = list(x_won_board)
        game = make_game(board, [(4, 0, "x")])  # Forces O to board 0 where two moves are legal.

        bot = get_bot("graph_puct_v1")
        result = bot.choose_move(game, SearchBudget(max_seconds=2, max_nodes=5), metadata=True, verbose=False)
        self.assertIsNotNone(result)
        metadata = result[2]
        self.assertEqual(metadata.get("search_type"), "exact_endgame")
        self.assertEqual(len(metadata.get("moves", [])), 2)


if __name__ == "__main__":
    unittest.main()
