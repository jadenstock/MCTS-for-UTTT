from bots.baseline_mcts.bot import BaselineMCTSBot
from bots.baseline_mcts.config import BASELINE_PRESETS, DEFAULT_BOT_ID
from bots.pragmatic_mcts.bot import PragmaticMCTSBot
from bots.pragmatic_mcts.config import PRAGMATIC_PRESETS


def list_bot_ids():
    return sorted(set(BASELINE_PRESETS.keys()) | set(PRAGMATIC_PRESETS.keys()))


def get_bot(bot_id):
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
        else:
            cfg = BASELINE_PRESETS[bot_id]
            family = "baseline_mcts"
            notes = "Baseline family preset (same core algorithm, different parameter tuning)."
        summaries.append({
            "bot_id": bot_id,
            "family": family,
            "ucb_constant": cfg.get("ucb_constant"),
            "rollout_depth": cfg.get("rollout_depth"),
            "notes": notes,
        })
    return summaries
