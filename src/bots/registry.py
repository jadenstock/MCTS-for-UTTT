from bots.baseline_mcts.bot import BaselineMCTSBot
from bots.baseline_mcts.config import BASELINE_PRESETS, DEFAULT_BOT_ID


def list_bot_ids():
    return sorted(BASELINE_PRESETS.keys())


def get_bot(bot_id):
    selected_id = bot_id if bot_id in BASELINE_PRESETS else DEFAULT_BOT_ID
    return BaselineMCTSBot(selected_id)

