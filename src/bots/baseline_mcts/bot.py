from bots.base import Bot
from bots.baseline_mcts.config import get_preset
from bots.baseline_mcts.policy import BaselineMCTSPolicy
from search.mcts_core import run_mcts


class BaselineMCTSBot(Bot):
    def __init__(self, bot_id):
        self.bot_id = bot_id
        self.config = get_preset(bot_id)
        self.policy = BaselineMCTSPolicy(self.config)

    def choose_move(self, game, budget, metadata=True, verbose=False):
        return run_mcts(
            game=game,
            policy=self.policy,
            budget=budget,
            agent_id=self.bot_id,
            metadata=metadata,
            verbose=verbose,
        )

