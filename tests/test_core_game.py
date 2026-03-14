import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.game import Game, make_game


class TestCoreGame(unittest.TestCase):
    def test_make_game_allows_empty_move_stack(self):
        board = [["" for _ in range(9)] for _ in range(9)]
        game = make_game(board, [])
        self.assertEqual(game.next_to_move, "x")
        self.assertEqual(game.move_stack, [])
        self.assertEqual(game.legal_moves()[0], (0, 0))

    def test_board_str_does_not_crash(self):
        game = Game()
        board_text = str(game.board)
        self.assertIsInstance(board_text, str)
        self.assertGreater(len(board_text), 0)

    def test_make_move_and_undo_preserve_state(self):
        game = Game()
        self.assertTrue(game.make_move(4, 4, "x"))
        self.assertEqual(game.next_to_move, "o")
        self.assertEqual(game.move_stack[-1], (4, 4, "x"))
        self.assertTrue(game.undo_last_move())
        self.assertEqual(game.next_to_move, "x")
        self.assertEqual(game.move_stack, [])
        self.assertEqual(game.board.boards[4].cells[4], "")

    def test_board_score_returns_half_for_terminal_draw(self):
        game = Game()
        drawn_miniboard = ["x", "o", "x", "x", "o", "o", "o", "x", "x"]
        for mini_board in game.board.boards:
            mini_board.cells = list(drawn_miniboard)
        game.evaluate_winners()

        self.assertEqual(game.board.winner, "")
        self.assertEqual(game.legal_moves(), [])
        self.assertAlmostEqual(game.board.score("x"), 0.5, places=6)
        self.assertAlmostEqual(game.board.score("o"), 0.5, places=6)


if __name__ == "__main__":
    unittest.main()
