import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ai.mcts import SimulationTreeNode
from ai.mcts import evaluate_next_move
from core.game import Game, make_game


class TestMCTS(unittest.TestCase):
    def test_child_nodes_keep_agent_id(self):
        game = Game()
        node = SimulationTreeNode(game, "x", agent_id="aggressive")
        node.expand_one_child()

        self.assertGreater(len(node.children), 0)
        child = next(iter(node.children.values()))
        self.assertEqual(child.agent_id, "aggressive")

    def test_ucb_selection_minimizes_root_score_on_opponent_turn(self):
        game = Game()
        node = SimulationTreeNode(game, "x")
        game.next_to_move = "o"

        child_a = SimulationTreeNode(game, "x")
        child_b = SimulationTreeNode(game, "x")
        child_a.number_of_plays = 10
        child_b.number_of_plays = 10
        child_a.total_score = 9.0  # better for root player
        child_b.total_score = 2.0  # worse for root player

        node.children = {(0, 0): child_a, (0, 1): child_b}
        node.number_of_plays = 50

        best = node.get_best_action_by_ucb1(C=1.414)
        self.assertEqual(best, (0, 1))

    def test_avoids_sending_opponent_to_immediate_local_win_when_safe_option_exists(self):
        # Last move sends O to board 5.
        board = [
            ["x", "x", "", "", "", "", "", "", ""],  # X can win board 0 immediately by playing cell 2
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "x", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
        ]
        move_stack = [(4, 5, "x")]
        game = make_game(board, move_stack)

        # O is forced to board 5. Move (5, 0) sends X to board 0 where X has an immediate local win.
        self.assertIn((5, 0), game.legal_moves())
        result = evaluate_next_move(game, seconds_limit=1, node_limit=80, verbose=False)
        self.assertNotEqual((result[0], result[1]), (5, 0))


if __name__ == "__main__":
    unittest.main()
