import math
import time


DEFAULT_SECONDS_LIMIT = 30
DEFAULT_NODE_LIMIT = 100000


class SimulationTreeNode:
    def __init__(self, game, player, policy, agent_id="default"):
        self.game = game
        self.player = player
        self.policy = policy
        self.agent_id = agent_id
        self.number_of_plays = 1
        self.children = {}
        self.total_score = 0.0
        self.depth_seen = 1
        self.unseen_children = list(game.legal_moves())
        self.ucb_constant = float(policy.ucb_constant)
        self.rollout_depth = int(policy.rollout_depth)

    def get_score_of_move(self, move):
        child = self.children.get(move)
        if child is None:
            return None
        return float(child.total_score) / float(child.number_of_plays)

    def get_best_action_by_ucb1(self, c=None, C=None):
        if c is None:
            c = C if C is not None else self.ucb_constant
        maximize_root_score = self.game.next_to_move == self.player
        action = None
        best_score = -float("inf")
        for move, child in self.children.items():
            mean_root_score = child.total_score / float(child.number_of_plays)
            exploit = mean_root_score if maximize_root_score else (1.0 - mean_root_score)
            # Standard UCB1 exploration pressure (less aggressive than prior scaling).
            explore = c * math.sqrt(2 * math.log(self.number_of_plays) / float(child.number_of_plays))
            ucb = exploit + explore
            if ucb > best_score:
                best_score = ucb
                action = move
            elif ucb == best_score and action is not None and move < action:
                action = move
        return action

    def expand_one_child(self, game_path=None):
        if game_path is None:
            game_path = []
        if not self.unseen_children:
            return

        move = self.unseen_children.pop()
        moves_made = []
        self.game.make_move(move[0], move[1], self.game.next_to_move)
        moves_made.append(move)

        self.children[move] = SimulationTreeNode(
            game=self.game,
            player=self.player,
            policy=self.policy,
            agent_id=self.agent_id,
        )

        depth = 0
        while depth < self.rollout_depth and not self.game.board.winner and self.game.legal_moves():
            rollout_move = self.policy.rollout_move(self.game)
            if not rollout_move:
                break
            self.game.make_move(rollout_move[0], rollout_move[1], self.game.next_to_move)
            moves_made.append(rollout_move)
            depth += 1

        score = self.policy.evaluate(self.game, self.player)
        self.children[move].total_score = score

        for node in game_path + [self]:
            node.number_of_plays += 1
            node.total_score += score
            if len(game_path) > node.depth_seen:
                node.depth_seen = len(game_path)

        for _ in range(len(moves_made)):
            self.game.undo_last_move()

    def expand_tree_by_one(self, game_path=None):
        if game_path is None:
            game_path = []
        if self.unseen_children:
            self.expand_one_child(game_path=game_path)
            return
        if self.children:
            move = self.get_best_action_by_ucb1(self.ucb_constant)
            self.game.make_move(move[0], move[1], self.game.next_to_move)
            self.children[move].expand_tree_by_one(game_path=game_path + [self])
            self.game.undo_last_move()


def _make_single_move_metadata(game, move, policy):
    player = game.next_to_move
    game.make_move(move[0], move[1], player)
    forced_score = policy.evaluate(game, player)
    game.undo_last_move()
    return {
        "num_gamestates": 0,
        "depth_explored": 0,
        "moves": [(move, forced_score, 0)],
        "thinking_time": 0.0,
        "early_stop": True,
    }


def run_mcts(
    game,
    policy,
    budget,
    agent_id="default",
    metadata=True,
    verbose=False,
):
    legal = game.legal_moves()
    if not legal:
        return None
    if len(legal) == 1:
        move = legal[0]
        if metadata:
            return [move[0], move[1], _make_single_move_metadata(game, move, policy)]
        return move

    node = SimulationTreeNode(game=game, player=game.next_to_move, policy=policy, agent_id=agent_id)
    start_time = time.time()
    max_seconds = float(getattr(budget, "max_seconds", DEFAULT_SECONDS_LIMIT))
    max_nodes = int(getattr(budget, "max_nodes", DEFAULT_NODE_LIMIT))

    while (time.time() - start_time <= max_seconds) and (node.number_of_plays < max_nodes):
        node.expand_tree_by_one()

    best_move = policy.select_final_move(game, node)
    if best_move is None:
        return None

    if not metadata:
        return best_move

    move_summaries = [
        (move, node.get_score_of_move(move), int(node.children[move].number_of_plays))
        for move in node.children
    ]
    move_metadata = {
        "num_gamestates": node.number_of_plays,
        "depth_explored": node.depth_seen,
        "moves": sorted(move_summaries, key=lambda x: (x[1], x[2]), reverse=True),
        "thinking_time": time.time() - start_time,
        "early_stop": False,
    }

    if verbose:
        print(f"number of gamestates evaluated: {move_metadata['num_gamestates']}")
        print(f"depth of game tree explored: {move_metadata['depth_explored']}")
        print(f"best move for {game.next_to_move}: {best_move}")
        best_child = node.children[best_move]
        print(f"score of best move: {best_child.total_score / float(best_child.number_of_plays)}")
        print("top moves:")
        for move, score, rollouts in move_metadata["moves"]:
            print(f"\tmove: {move}\tnum_plays: {rollouts}\tscore: {score}")

    return [best_move[0], best_move[1], move_metadata]
