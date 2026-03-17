import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.game import Game
from search.exact_endgame import count_legal_cells, solve_root_exact


class TestExactEndgame(unittest.TestCase):
    def test_count_legal_cells_ignores_won_or_drawn_boards(self):
        game = Game()
        game.board.boards[0].winner = "x"
        game.board.boards[0].cells = [""] * 9
        game.board.boards[1].winner = "draw"
        game.board.boards[1].cells = [""] * 9
        game.board.boards[2].winner = ""
        game.board.boards[2].cells = ["x", "", "o", "", "", "", "", "", ""]

        # Board 0/1 empties should be ignored; board 2 contributes 7 empties,
        # remaining boards contribute 6 * 9 empties.
        self.assertEqual(count_legal_cells(game), 7 + (6 * 9))

    def test_exact_solver_uses_configured_draw_value_for_single_legal_move(self):
        game = Game()
        # Exactly one legal move remains. That move fills the final open cell and
        # results in a draw (no global winner).
        for idx, mini in enumerate(game.board.boards):
            if idx == 0:
                mini.cells = ["", "x", "o", "o", "x", "x", "x", "o", "o"]
                mini.winner = ""
            else:
                mini.cells = ["x", "o", "x", "x", "o", "o", "o", "x", "x"]
                mini.winner = "draw"
        game.board.winner = ""
        game.next_to_move = "x"

        best_move, values, _stats = solve_root_exact(game, root_player="x", draw_value=0.25)
        self.assertEqual(best_move, (0, 0))
        self.assertIn((0, 0), values)
        self.assertAlmostEqual(values[(0, 0)], 0.25, places=6)

    def test_exact_solver_can_truncate_on_node_budget(self):
        game = Game()
        best_move, _values, stats = solve_root_exact(game, root_player="x", draw_value=0.5, max_nodes=1)
        self.assertIsNone(best_move)
        self.assertTrue(stats.truncated)


if __name__ == "__main__":
    unittest.main()
