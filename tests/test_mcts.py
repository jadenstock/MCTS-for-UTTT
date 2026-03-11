import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ai.mcts import SimulationTreeNode
from core.game import Game


class TestMCTS(unittest.TestCase):
    def test_child_nodes_keep_agent_id(self):
        game = Game()
        node = SimulationTreeNode(game, "x", agent_id="aggressive")
        node.expand_one_child()

        self.assertGreater(len(node.children), 0)
        child = next(iter(node.children.values()))
        self.assertEqual(child.agent_id, "aggressive")


if __name__ == "__main__":
    unittest.main()
