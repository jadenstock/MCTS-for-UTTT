import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from utils.elo_ratings import EloRatings


class TestEloRatings(unittest.TestCase):
    def test_initializes_all_tiers_and_default_ratings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ratings_path = Path(tmpdir) / "elo.json"
            elo = EloRatings(file_path=str(ratings_path), tiers=(200, 500, 800))

            self.assertEqual(elo.get_rating(200, "default"), 1200.0)
            self.assertEqual(elo.get_rating(500, "default"), 1200.0)
            self.assertEqual(elo.get_rating(800, "default"), 1200.0)

            with open(ratings_path) as f:
                data = json.load(f)
            self.assertIn("200", data["tiers"])
            self.assertIn("500", data["tiers"])
            self.assertIn("800", data["tiers"])

    def test_updates_only_target_tier(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ratings_path = Path(tmpdir) / "elo.json"
            elo = EloRatings(file_path=str(ratings_path), tiers=(200, 500, 800))
            before_500 = elo.get_rating(500, "default")
            before_800 = elo.get_rating(800, "graph_puct_v1")

            update = elo.update_result(200, "default", "graph_puct_v1", 1.0)

            self.assertGreater(update.new_a, update.old_a)
            self.assertLess(update.new_b, update.old_b)
            self.assertEqual(elo.get_rating(500, "default"), before_500)
            self.assertEqual(elo.get_rating(800, "graph_puct_v1"), before_800)


if __name__ == "__main__":
    unittest.main()
