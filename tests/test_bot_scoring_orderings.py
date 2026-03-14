import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bots.registry import get_bot, list_bot_ids


TEST_BOARDS = {
    "empty": [""] * 9,
    "x_center": ["", "", "", "", "X", "", "", "", ""],
    "x_corner": ["X", "", "", "", "", "", "", "", ""],
    "early_battle": ["X", "", "", "", "O", "", "", "", ""],
    "x_strong": ["X", "X", "", "O", "", "", "X", "", ""],
    "x_winning": ["X", "X", "", "O", "O", "", "X", "", ""],
    "o_winning": ["X", "", "", "O", "O", "", "X", "X", "O"],
    "x_won": ["X", "X", "X", "O", "O", "", "", "", ""],
    "drawn": ["X", "O", "X", "X", "O", "O", "O", "X", "X"],
}


class TestBotScoringOrderings(unittest.TestCase):
    def _check_reasonable_orderings(self, bot_id):
        bot = get_bot(bot_id)
        score = bot.policy.score_local_board

        scores = {
            name: (score(board, "X"), score(board, "O"))
            for name, board in TEST_BOARDS.items()
        }

        self.assertEqual(scores["x_won"][0], 1.0, f"{bot_id}: X should score 1.0 when X has won")
        self.assertEqual(scores["x_won"][1], 0.0, f"{bot_id}: O should score 0.0 when O has lost")
        self.assertEqual(scores["drawn"][0], 0.0, f"{bot_id}: X local draw score should be 0.0")
        self.assertEqual(scores["drawn"][1], 0.0, f"{bot_id}: O local draw score should be 0.0")
        self.assertGreater(scores["x_center"][0], scores["x_corner"][0], f"{bot_id}: center should outrank corner")
        self.assertGreater(scores["x_strong"][0], scores["x_center"][0], f"{bot_id}: strong board should outrank center")
        self.assertGreater(
            scores["x_winning"][0], scores["early_battle"][0], f"{bot_id}: winning board should outrank early battle"
        )
        self.assertGreater(scores["o_winning"][1], scores["o_winning"][0], f"{bot_id}: O winning should favor O")

    def test_registered_bots_pass_reasonable_orderings(self):
        for bot_id in list_bot_ids():
            with self.subTest(bot_id=bot_id):
                self._check_reasonable_orderings(bot_id)


if __name__ == "__main__":
    unittest.main()

