import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bots.registry import get_bot, list_bot_ids
from core.game import make_game


class TestDrawHaterBot(unittest.TestCase):
    def test_draw_hater_is_registered(self):
        self.assertIn("draw_hater", list_bot_ids())

    def test_draw_hater_values_draws_lower_than_default(self):
        drawn_miniboard = ["x", "o", "x", "x", "o", "o", "o", "x", "x"]
        board = [list(drawn_miniboard) for _ in range(9)]
        game = make_game(board, [])

        self.assertEqual(game.board.winner, "draw")

        default_bot = get_bot("default")
        draw_hater_bot = get_bot("draw_hater")

        default_score = default_bot.policy.evaluate(game, "x")
        draw_hater_score = draw_hater_bot.policy.evaluate(game, "x")

        self.assertAlmostEqual(default_score, 0.5, places=6)
        self.assertLess(draw_hater_score, default_score)
        self.assertAlmostEqual(draw_hater_score, 0.35, places=6)


if __name__ == "__main__":
    unittest.main()
