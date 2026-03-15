import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.benchmark import run_benchmark


class TestBenchmark(unittest.TestCase):
    def test_benchmark_reproducible_with_same_seed(self):
        def choose_first_legal(game, agent_id="default", seconds_limit=60, node_limit=100, verbose=False, metadata=False):
            legal = game.legal_moves()
            return legal[0] if legal else None

        # Keep unit test fast: deterministic mocked move policy.
        with patch("core.benchmark.evaluate_next_move", side_effect=choose_first_legal):
            with redirect_stdout(io.StringIO()):
                result1 = run_benchmark(
                    agent_a="default",
                    agent_b="aggressive",
                    games=4,
                    compute_time=60,
                    node_limit=40,
                    opening_random_plies=2,
                    seed=123,
                    update_elo=False,
                )
            with redirect_stdout(io.StringIO()):
                result2 = run_benchmark(
                    agent_a="default",
                    agent_b="aggressive",
                    games=4,
                    compute_time=60,
                    node_limit=40,
                    opening_random_plies=2,
                    seed=123,
                    update_elo=False,
                )

        self.assertEqual(result1, result2)

    def test_benchmark_updates_elo_for_tracked_tier(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            elo_path = Path(tmpdir) / "elo.json"
            with patch("core.benchmark._play_game", return_value=("x", 12)):
                with redirect_stdout(io.StringIO()):
                    run_benchmark(
                        agent_a="default",
                        agent_b="graph_puct_v1",
                        games=1,
                        compute_time=1,
                        node_limit=200,
                        opening_random_plies=0,
                        seed=7,
                        update_elo=True,
                        elo_file=str(elo_path),
                    )
            with open(elo_path) as f:
                data = json.load(f)
            ratings = data["tiers"]["200"]["agents"]
            self.assertGreater(ratings["default"], 1200.0)
            self.assertLess(ratings["graph_puct_v1"], 1200.0)

    def test_benchmark_rejects_untracked_tier_when_elo_enabled(self):
        with self.assertRaises(ValueError):
            run_benchmark(
                agent_a="default",
                agent_b="graph_puct_v1",
                games=1,
                compute_time=1,
                node_limit=250,
                opening_random_plies=0,
                seed=7,
                update_elo=True,
            )


if __name__ == "__main__":
    unittest.main()
