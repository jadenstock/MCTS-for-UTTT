import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.game import Game
from utils.game_storage import GameStorage


class TestGameStorage(unittest.TestCase):
    def test_save_game_handles_empty_move_stack(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = GameStorage(data_dir=tmpdir)
            game = Game()
            storage.save_game("empty-game", game)

            path = Path(tmpdir) / "empty-game.json"
            self.assertTrue(path.exists())
            data = json.loads(path.read_text())
            self.assertEqual(data["moves"], [])
            self.assertIsNone(data["current_state"]["last_move"])

    def test_save_game_appends_moves_once_per_save(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = GameStorage(data_dir=tmpdir)
            game = Game()

            game.make_move(4, 4, "x")
            storage.save_game("g1", game)

            game.make_move(4, 0, "o")
            storage.save_game("g1", game)

            data = storage.load_game("g1")
            self.assertEqual(len(data["moves"]), 2)
            self.assertEqual(data["moves"][0]["player"], "x")
            self.assertEqual(data["moves"][1]["player"], "o")


if __name__ == "__main__":
    unittest.main()
