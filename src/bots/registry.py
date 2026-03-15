from bots.baseline_mcts.bot import BaselineMCTSBot
from bots.baseline_mcts.config import BASELINE_PRESETS, DEFAULT_BOT_ID
from bots.graph_puct_mcts.bot import GraphPUCTMCTSBot
from bots.graph_puct_mcts.config import GRAPH_PUCT_PRESETS, GRAPH_PUCT_BOT_ID
from bots.pragmatic_mcts.bot import PragmaticMCTSBot
from bots.pragmatic_mcts.config import PRAGMATIC_PRESETS


def list_bot_ids():
    return sorted(set(BASELINE_PRESETS.keys()) | set(PRAGMATIC_PRESETS.keys()) | set(GRAPH_PUCT_PRESETS.keys()))


def get_bot(bot_id):
    if bot_id in GRAPH_PUCT_PRESETS:
        return GraphPUCTMCTSBot(bot_id)
    if bot_id in PRAGMATIC_PRESETS:
        return PragmaticMCTSBot(bot_id)
    selected_id = bot_id if bot_id in BASELINE_PRESETS else DEFAULT_BOT_ID
    return BaselineMCTSBot(selected_id)


def list_bot_summaries():
    summaries = []
    for bot_id in list_bot_ids():
        if bot_id in PRAGMATIC_PRESETS:
            cfg = PRAGMATIC_PRESETS[bot_id]
            family = "pragmatic_mcts"
            notes = "Tactical-biased revision with stronger immediate win/block priorities."
        elif bot_id in GRAPH_PUCT_PRESETS:
            cfg = GRAPH_PUCT_PRESETS[bot_id]
            family = "graph_puct_mcts"
            notes = "PUCT-guided graph search with transposition table across repeated states."
        else:
            cfg = BASELINE_PRESETS[bot_id]
            family = "baseline_mcts"
            notes = "Baseline family preset (same core algorithm, different parameter tuning)."
        summaries.append({
            "bot_id": bot_id,
            "family": family,
            "ucb_constant": cfg.get("ucb_constant", cfg.get("c_puct")),
            "rollout_depth": cfg.get("rollout_depth"),
            "notes": notes,
        })
    return summaries
