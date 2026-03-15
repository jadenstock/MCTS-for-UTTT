from bots.base import Bot
from bots.graph_puct_mcts.config import get_preset
from bots.graph_puct_mcts.policy import GraphPUCTPolicy
from search.graph_puct_core import run_graph_puct


class GraphPUCTMCTSBot(Bot):
    def __init__(self, bot_id):
        self.bot_id = bot_id
        self.config = get_preset(bot_id)
        self.policy = GraphPUCTPolicy(self.config)

    def choose_move(self, game, budget, metadata=True, verbose=False):
        return run_graph_puct(
            game=game,
            policy=self.policy,
            budget=budget,
            metadata=metadata,
            verbose=verbose,
        )

