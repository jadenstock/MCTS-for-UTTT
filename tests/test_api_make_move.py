import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from importlib.util import find_spec

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

FLASK_AVAILABLE = find_spec("flask") is not None
if FLASK_AVAILABLE:
    import flask_server
    from utils.game_storage import GameStorage


@unittest.skipUnless(FLASK_AVAILABLE, "Flask dependency is not installed")
class TestMakeMoveAPI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        flask_server.storage = GameStorage(data_dir=self.tmp.name)
        self.client = flask_server.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    @patch("flask_server.evaluate_next_move")
    def test_make_move_persists_two_moves_without_duplication(self, mock_eval):
        mock_eval.return_value = [4, 0, {"num_gamestates": 1, "depth_explored": 1, "moves": [], "thinking_time": 0.0, "early_stop": False}]

        payload = {
            "game_id": "g-authoritative",
            "last_move": [4, 4, "X"],
            "game_board": [["" for _ in range(9)] for _ in range(9)],
            "compute_time": 1,
            "force_full_time": False,
        }

        res = self.client.post("/api/makemove/", json=payload)
        self.assertEqual(res.status_code, 200)
        body = res.get_json()

        self.assertEqual(body["board"], 4)
        self.assertEqual(body["cell"], 0)
        self.assertEqual(body["move_count"], 2)
        self.assertEqual(body["current_state"]["last_move"], [4, 0, "o"])
        self.assertEqual(body["current_state"]["next_to_move"], "x")

        saved = flask_server.storage.load_game("g-authoritative")
        self.assertEqual(len(saved["moves"]), 2)
        self.assertEqual(saved["moves"][0]["player"], "x")
        self.assertEqual(saved["moves"][1]["player"], "o")

    @patch("flask_server.evaluate_next_move")
    def test_make_move_rejects_illegal_human_move_from_loaded_state(self, mock_eval):
        mock_eval.return_value = [4, 0, {"num_gamestates": 1, "depth_explored": 1, "moves": [], "thinking_time": 0.0, "early_stop": False}]

        first = {
            "game_id": "g-illegal",
            "last_move": [4, 4, "X"],
            "game_board": [["" for _ in range(9)] for _ in range(9)],
            "compute_time": 1,
            "force_full_time": False,
        }
        ok = self.client.post("/api/makemove/", json=first)
        self.assertEqual(ok.status_code, 200)

        # After X: (4,4), O: (4,0), target board is 0. Playing on board 1 is illegal.
        illegal = {
            "game_id": "g-illegal",
            "last_move": [1, 1, "X"],
            "game_board": [["" for _ in range(9)] for _ in range(9)],
            "compute_time": 1,
            "force_full_time": False,
        }
        bad = self.client.post("/api/makemove/", json=illegal)
        self.assertEqual(bad.status_code, 400)
        self.assertIn("Illegal human move", bad.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
