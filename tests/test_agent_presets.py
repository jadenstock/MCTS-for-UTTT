import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bots.baseline_mcts.config import get_preset as get_baseline_preset
from bots.graph_puct_mcts.config import get_preset as get_graph_puct_preset
from bots.registry import list_bot_ids


class TestAgentPresets(unittest.TestCase):
    def test_new_baseline_exact_presets_registered(self):
        ids = list_bot_ids()
        self.assertIn("default_exact_legal10_draw050_v1", ids)
        self.assertIn("default_exact_legal14_draw050_v1", ids)
        self.assertIn("default_exact_legal10_draw025_v1", ids)

    def test_new_graph_puct_exact_presets_registered(self):
        ids = list_bot_ids()
        self.assertIn("graph_puct_legal6_draw025_v2", ids)
        self.assertIn("graph_puct_legal10_draw050_v2", ids)
        self.assertIn("graph_puct_legal14_draw050_v2", ids)
        self.assertIn("graph_puct_legal10_draw025_v2", ids)
        self.assertIn("graph_puct_legal14_draw025_v2", ids)
        self.assertIn("graph_puct_legal18_draw025_v2", ids)
        self.assertIn("graph_puct_legal10_draw000_v2", ids)
        self.assertIn("graph_puct_legal14_draw000_v2", ids)
        self.assertIn("graph_puct_legal18_draw000_v2", ids)

    def test_graph_preset_lookup_uses_requested_id(self):
        p = get_graph_puct_preset("graph_puct_legal10_draw025_v2")
        self.assertEqual(float(p.get("terminal_draw_value")), 0.25)
        self.assertEqual(int(p.get("exact_endgame_legal_cells_threshold")), 10)
        p_zero = get_graph_puct_preset("graph_puct_legal18_draw000_v2")
        self.assertEqual(float(p_zero.get("terminal_draw_value")), 0.0)
        self.assertEqual(int(p_zero.get("exact_endgame_legal_cells_threshold")), 18)
        p_t6 = get_graph_puct_preset("graph_puct_legal6_draw025_v2")
        self.assertEqual(float(p_t6.get("terminal_draw_value")), 0.25)
        self.assertEqual(int(p_t6.get("exact_endgame_legal_cells_threshold")), 6)

    def test_baseline_preset_lookup_uses_requested_id(self):
        p = get_baseline_preset("default_exact_legal14_draw050_v1")
        self.assertEqual(float(p.get("terminal_draw_value")), 0.5)
        self.assertEqual(int(p.get("exact_endgame_legal_cells_threshold")), 14)


if __name__ == "__main__":
    unittest.main()
