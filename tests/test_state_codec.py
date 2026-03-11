import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.game import Game
from core.state_codec import serialize_game_state, game_from_current_state, replay_game_from_moves


class TestStateCodec(unittest.TestCase):
    def test_serialize_and_restore_current_state(self):
        game = Game()
        game.make_move(4, 4, "x")
        game.make_move(4, 0, "o")

        state = serialize_game_state(game)
        restored = game_from_current_state(state)

        self.assertEqual(restored.next_to_move, game.next_to_move)
        self.assertEqual(restored.move_stack[-1], game.move_stack[-1])
        self.assertEqual([b.cells for b in restored.board.boards], [b.cells for b in game.board.boards])

    def test_replay_game_from_moves(self):
        moves = [
            {"board": 4, "cell": 4, "player": "x"},
            {"board": 4, "cell": 0, "player": "o"},
            {"board": 0, "cell": 8, "player": "x"},
        ]
        game = replay_game_from_moves(moves)

        self.assertEqual(len(game.move_stack), 3)
        self.assertEqual(game.move_stack[-1], (0, 8, "x"))
        self.assertEqual(game.next_to_move, "o")


if __name__ == "__main__":
    unittest.main()
