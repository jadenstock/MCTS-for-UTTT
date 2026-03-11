import io
import sys
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
                )

        self.assertEqual(result1, result2)


if __name__ == "__main__":
    unittest.main()
