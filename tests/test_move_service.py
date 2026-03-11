import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.move_service import apply_human_and_ai_move
from utils.game_storage import GameStorage


class TestMoveService(unittest.TestCase):
    def test_apply_human_and_ai_move_persists_exactly_two_moves(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = GameStorage(data_dir=tmpdir)

            def fake_eval(game, seconds_limit, verbose=False):
                # After human (4,4), target board is 4.
                return [4, 0, {"num_gamestates": 1}]

            res = apply_human_and_ai_move(
                storage=storage,
                game_id="svc-game",
                human_move=[4, 4, "X"],
                compute_time=1,
                evaluate_fn=fake_eval,
            )

            self.assertEqual(res["board"], 4)
            self.assertEqual(res["cell"], 0)
            self.assertEqual(res["move_count"], 2)

            saved = storage.load_game("svc-game")
            self.assertEqual(len(saved["moves"]), 2)
            self.assertEqual(saved["moves"][0]["player"], "x")
            self.assertEqual(saved["moves"][1]["player"], "o")

    def test_illegal_human_move_raises_value_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = GameStorage(data_dir=tmpdir)

            def fake_eval(game, seconds_limit, verbose=False):
                return [4, 0, {"num_gamestates": 1}]

            # First legal turn to establish target board=0.
            apply_human_and_ai_move(
                storage=storage,
                game_id="svc-illegal",
                human_move=[4, 4, "X"],
                compute_time=1,
                evaluate_fn=fake_eval,
            )

            with self.assertRaises(ValueError):
                apply_human_and_ai_move(
                    storage=storage,
                    game_id="svc-illegal",
                    human_move=[1, 1, "X"],
                    compute_time=1,
                    evaluate_fn=fake_eval,
                )


if __name__ == "__main__":
    unittest.main()
