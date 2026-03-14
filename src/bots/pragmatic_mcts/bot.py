from bots.base import Bot
from bots.pragmatic_mcts.config import get_preset
from bots.pragmatic_mcts.policy import PragmaticMCTSPolicy
from search.mcts_core import run_mcts


class PragmaticMCTSBot(Bot):
    def __init__(self, bot_id):
        self.bot_id = bot_id
        self.config = get_preset(bot_id)
        self.policy = PragmaticMCTSPolicy(self.config)

    def choose_move(self, game, budget, metadata=True, verbose=False):
        return run_mcts(
            game=game,
            policy=self.policy,
            budget=budget,
            agent_id=self.bot_id,
            metadata=metadata,
            verbose=verbose,
        )

