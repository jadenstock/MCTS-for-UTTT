from bots.base import SearchBudget
from bots.registry import get_bot
from search.mcts_core import DEFAULT_NODE_LIMIT, DEFAULT_SECONDS_LIMIT, SimulationTreeNode as CoreSimulationTreeNode


class SimulationTreeNode(CoreSimulationTreeNode):
    """Compatibility wrapper for tests and legacy imports."""

    def __init__(self, game, player, agent_id="default"):
        bot = get_bot(agent_id)
        super().__init__(game=game, player=player, policy=bot.policy, agent_id=agent_id)


def evaluate_next_move(
    game,
    agent_id="default",
    seconds_limit=DEFAULT_SECONDS_LIMIT,
    node_limit=DEFAULT_NODE_LIMIT,
    verbose=True,
    metadata=True,
):
    bot = get_bot(agent_id)
    budget = SearchBudget(max_seconds=float(seconds_limit), max_nodes=int(node_limit))
    return bot.choose_move(game=game, budget=budget, metadata=metadata, verbose=verbose)

