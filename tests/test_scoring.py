import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from utils.game_score_utils import score_board, calculate_square_importance


class TestScoring(unittest.TestCase):
    def test_score_board_is_case_insensitive(self):
        board_upper = ["X", "X", "", "", "", "", "", "", ""]
        board_lower = ["x", "x", "", "", "", "", "", "", ""]

        upper_score = score_board(board_upper, "X")
        lower_score = score_board(board_lower, "x")
        self.assertAlmostEqual(upper_score, lower_score, places=6)

    def test_square_importance_accepts_lowercase_tokens(self):
        board = ["x", "", "", "", "", "", "", "", ""]
        imp_x, imp_o = calculate_square_importance(board)
        self.assertEqual(len(imp_x), 9)
        self.assertEqual(len(imp_o), 9)
        self.assertTrue(any(value > 0 for value in imp_x))


if __name__ == "__main__":
    unittest.main()
