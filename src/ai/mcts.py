import time
import math
from utils.utils import load_agent_config

DEFAULT_SECONDS_LIMIT = 30
DEFAULT_NODE_LIMIT = 100000


class SimulationTreeNode:
    def __init__(self, game, player, agent_id='default'):
        self.game = game
        self.player = player
        self.number_of_plays = 1
        self.children = {}
        self.total_score = 0
        self.depth_seen = 1
        self.unseen_children = list(game.legal_moves())

        config = load_agent_config(agent_id=agent_id)
        self.ucb_constant = float(config.get("ucb_constant", 1.414))
        self.rollout_depth = int(config.get("rollout_depth", 5))

    def get_score_of_move(self, m):
        if m not in self.children:
            print("{} is not a move from this state".format(m))
            return
        return float(self.children[m].total_score) / float(self.children[m].number_of_plays)

    def get_best_action_by_average_score(self):
        action = None
        best_score = -float("inf")
        for m, c in self.children.items():
            score = c.total_score / float(c.number_of_plays)
            if score >= best_score:
                best_score = score
                action = m
        return action

    def get_best_action_by_ucb1(self, C):
        action = None
        best_score = -float("inf")
        for m, c in self.children.items():
            exploit = c.total_score / float(c.number_of_plays)
            explore = 2 * C * math.sqrt(2 * math.log(self.number_of_plays) / float(c.number_of_plays))
            ucb = exploit + explore
            if ucb >= best_score:
                best_score = ucb
                action = m
        return action

    def expand_one_child(self, game_path=[]):
        if len(self.unseen_children) == 0:
            return

        # Get move to try
        m = self.unseen_children.pop()
        moves_made = []

        # Make the move
        self.game.make_move(m[0], m[1], self.game.next_to_move)
        moves_made.append(m)

        # Create child node
        self.children[m] = SimulationTreeNode(self.game, self.player)

        # Run quick simulation
        depth = 0
        while depth < self.rollout_depth and not self.game.board.winner and self.game.legal_moves():
            greedy_move = self.game.greedy_next_move()
            if not greedy_move:
                break
            self.game.make_move(greedy_move[0], greedy_move[1], self.game.next_to_move)
            moves_made.append(greedy_move)
            depth += 1

        # Get score at this depth
        score = self.game.board.score(self.player)
        self.children[m].total_score = score

        # Backpropagate
        for node in game_path:
            node.number_of_plays += 1
            node.total_score += score
            if len(game_path) > node.depth_seen:
                node.depth_seen = len(game_path)

        # Undo all moves
        for _ in range(len(moves_made)):
            self.game.undo_last_move()

    def expand_tree_by_one(self, game_path=[]):
        if len(self.unseen_children) != 0:
            self.expand_one_child(game_path=game_path)
        else:
            if len(self.children) > 0:
                m = self.get_best_action_by_ucb1(self.ucb_constant)
                # Make move
                self.game.make_move(m[0], m[1], self.game.next_to_move)
                # Expand child
                # TODO: Consider some sort of UCB constant schedule
                self.children[m].expand_tree_by_one(game_path=game_path + [self])
                # Undo move
                self.game.undo_last_move()


def evaluate_next_move(game,
                       agent_id='default',
                       seconds_limit=DEFAULT_SECONDS_LIMIT,
                       node_limit=DEFAULT_NODE_LIMIT,
                       verbose=True,
                       metadata=True):
    """Main MCTS driver function with same interface as original."""

    node = SimulationTreeNode(game, game.next_to_move, agent_id=agent_id)
    start_time = time.time()

    # Main MCTS loop
    while (time.time() - start_time <= seconds_limit) and (node.number_of_plays < node_limit):
        # Dynamic UCB constant based on remaining time
        elapsed = time.time() - start_time
        # time_ratio = elapsed / seconds_limit
        node.expand_tree_by_one()

    best_move = node.get_best_action_by_average_score()

    if metadata:
        move_metadata = {
            "num_gamestates": node.number_of_plays,
            "depth_explored": node.depth_seen,
            "moves": sorted([(m, node.get_score_of_move(m)) for m in node.children],
                            key=lambda x: x[1])[::-1],
            "thinking_time": time.time() - start_time,
            "early_stop": False  # Simplified to always use full time
        }

        if verbose:
            print("number of gamestates evaluated: {}".format(move_metadata["num_gamestates"]))
            print("depth of game tree explored: {}".format(move_metadata["depth_explored"]))
            print("best move for {}: {}".format(game.next_to_move, best_move))
            print("score of best move: {}".format(
                node.children[best_move].total_score / float(node.children[best_move].number_of_plays)))
            print("top moves:\n")
            for m, s in move_metadata["moves"]:
                print("\tmove: {}\tnum_plays: {}\tscore: {}".format(m, node.children[m].number_of_plays, s))

        return [best_move[0], best_move[1], move_metadata]
    return best_move