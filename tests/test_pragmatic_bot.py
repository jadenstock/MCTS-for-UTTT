import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bots.base import SearchBudget
from bots.registry import get_bot, list_bot_ids
from core.game import make_game


class TestPragmaticBot(unittest.TestCase):
    def test_pragmatic_bot_is_registered(self):
        self.assertIn("pragmatic_v1", list_bot_ids())

    def test_pragmatic_takes_immediate_global_win(self):
        board = [["" for _ in range(9)] for _ in range(9)]
        board[0] = ["o", "o", "", "", "", "", "", "", ""]
        board[1] = ["o", "o", "o", "", "", "", "", "", ""]
        board[2] = ["o", "o", "o", "", "", "", "", "", ""]
        board[4][0] = "x"

        game = make_game(board, [(4, 0, "x")])
        self.assertEqual(game.next_to_move, "o")
        self.assertIn((0, 2), game.legal_moves())

        bot = get_bot("pragmatic_v1")
        result = bot.choose_move(game, SearchBudget(max_seconds=5, max_nodes=150), metadata=False, verbose=False)
        self.assertEqual(result, (0, 2))


if __name__ == "__main__":
    unittest.main()

