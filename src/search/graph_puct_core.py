import math
import time
from dataclasses import dataclass, field


DEFAULT_SECONDS_LIMIT = 30
DEFAULT_NODE_LIMIT = 100000


@dataclass
class GraphNodeStats:
    priors: dict
    visits: int = 0
    value_sum: float = 0.0
    edge_visits: dict = field(default_factory=dict)
    edge_value_sum: dict = field(default_factory=dict)

    def edge_q(self, move):
        n = self.edge_visits.get(move, 0)
        if n <= 0:
            return 0.5
        return self.edge_value_sum.get(move, 0.0) / float(n)


class RootGraphView:
    def __init__(self, stats):
        self.stats = stats
        self.edge_visits = stats.edge_visits

    def edge_q(self, move):
        return self.stats.edge_q(move)


def _state_key(game):
    last_cell = game.move_stack[-1][1] if game.move_stack else -1
    boards = tuple(tuple(mini.cells) for mini in game.board.boards)
    winners = tuple(mini.winner for mini in game.board.boards)
    return (boards, winners, game.board.winner, game.next_to_move, last_cell)


def _ensure_node(graph, key, game, policy):
    if key in graph:
        return graph[key]
    legal = game.legal_moves()
    priors = policy.priors(game, legal) if legal else {}
    node = GraphNodeStats(priors=priors)
    node.edge_visits = {m: 0 for m in legal}
    node.edge_value_sum = {m: 0.0 for m in legal}
    graph[key] = node
    return node


def _select_puct_move(node, game, root_player, c_puct):
    legal = game.legal_moves()
    if not legal:
        return None
    maximize_root = game.next_to_move == root_player
    sqrt_n = math.sqrt(max(1, node.visits))
    best_move = None
    best_score = -float("inf")
    for move in legal:
        q = node.edge_q(move)
        q_eff = q if maximize_root else (1.0 - q)
        p = node.priors.get(move, 1e-3)
        n = node.edge_visits.get(move, 0)
        u = c_puct * p * (sqrt_n / (1 + n))
        s = q_eff + u
        if s > best_score:
            best_score = s
            best_move = move
        elif s == best_score and best_move is not None and move < best_move:
            best_move = move
    return best_move


def _rollout(game, policy, root_player):
    moves_made = []
    depth = 0
    while depth < policy.rollout_depth and not game.board.winner and game.legal_moves():
        move = policy.rollout_move(game)
        if not move:
            break
        game.make_move(move[0], move[1], game.next_to_move)
        moves_made.append(move)
        depth += 1
    value = policy.evaluate(game, root_player)
    for _ in range(len(moves_made)):
        game.undo_last_move()
    return value


def _run_simulation(game, policy, graph, root_player, forced_root_move=None):
    path = []
    moves_made = []
    depth = 0
    key = _state_key(game)
    node = _ensure_node(graph, key, game, policy)

    if forced_root_move is not None:
        legal_moves = game.legal_moves()
        if forced_root_move not in legal_moves:
            return 0
        move = forced_root_move
        path.append((key, move))
        game.make_move(move[0], move[1], game.next_to_move)
        moves_made.append(move)
        depth += 1
        key = _state_key(game)
        if key not in graph:
            _ensure_node(graph, key, game, policy)
            leaf_value = _rollout(game, policy, root_player)
            for state_key, backed_move in path:
                n = graph[state_key]
                n.visits += 1
                n.value_sum += leaf_value
                n.edge_visits[backed_move] = n.edge_visits.get(backed_move, 0) + 1
                n.edge_value_sum[backed_move] = n.edge_value_sum.get(backed_move, 0.0) + leaf_value
            for _ in range(len(moves_made)):
                game.undo_last_move()
            return depth
        node = graph[key]

    while True:
        legal_moves = game.legal_moves()
        if not legal_moves or game.board.winner:
            leaf_value = policy.evaluate(game, root_player)
            break

        move = _select_puct_move(node, game, root_player, policy.c_puct)
        if move is None:
            leaf_value = policy.evaluate(game, root_player)
            break

        path.append((key, move))
        game.make_move(move[0], move[1], game.next_to_move)
        moves_made.append(move)
        depth += 1
        key = _state_key(game)
        if key not in graph:
            node = _ensure_node(graph, key, game, policy)
            leaf_value = _rollout(game, policy, root_player)
            break
        node = graph[key]

    # Backup
    for state_key, move in path:
        n = graph[state_key]
        n.visits += 1
        n.value_sum += leaf_value
        n.edge_visits[move] = n.edge_visits.get(move, 0) + 1
        n.edge_value_sum[move] = n.edge_value_sum.get(move, 0.0) + leaf_value

    # A terminal/root-only evaluation still counts as one root visit.
    if not path:
        root_key = _state_key(game)
        root = graph[root_key]
        root.visits += 1
        root.value_sum += leaf_value

    for _ in range(len(moves_made)):
        game.undo_last_move()
    return depth


def run_graph_puct(
    game,
    policy,
    budget,
    metadata=True,
    verbose=False,
):
    legal = game.legal_moves()
    if not legal:
        return None
    if len(legal) == 1:
        move = legal[0]
        if not metadata:
            return move
        player = game.next_to_move
        game.make_move(move[0], move[1], player)
        s = policy.evaluate(game, player)
        game.undo_last_move()
        return [move[0], move[1], {
            "num_gamestates": 0,
            "depth_explored": 0,
            "moves": [(move, s, 0)],
            "thinking_time": 0.0,
            "early_stop": True,
        }]

    root_player = game.next_to_move
    graph = {}
    root_key = _state_key(game)
    root = _ensure_node(graph, root_key, game, policy)

    start_time = time.time()
    max_seconds = float(getattr(budget, "max_seconds", DEFAULT_SECONDS_LIMIT))
    max_nodes = int(getattr(budget, "max_nodes", DEFAULT_NODE_LIMIT))
    iterations = 0
    max_depth = 0

    # Ensure every legal root move is sampled at least once when budget allows.
    for root_move in legal:
        if (time.time() - start_time > max_seconds) or (iterations >= max_nodes):
            break
        if int(root.edge_visits.get(root_move, 0)) > 0:
            continue
        depth = _run_simulation(game, policy, graph, root_player, forced_root_move=root_move)
        max_depth = max(max_depth, depth)
        iterations += 1
        root = graph.get(root_key, root)

    while (time.time() - start_time <= max_seconds) and (iterations < max_nodes):
        depth = _run_simulation(game, policy, graph, root_player)
        max_depth = max(max_depth, depth)
        iterations += 1

    root = graph.get(root_key, root)
    best_move = policy.select_final_move(game, RootGraphView(root))
    if best_move is None:
        return None
    if not metadata:
        return best_move

    move_summaries = []
    for move in game.legal_moves():
        visits = int(root.edge_visits.get(move, 0))
        q_value = None if visits <= 0 else root.edge_q(move)
        move_summaries.append((
            move,
            q_value,
            visits,
        ))
    move_metadata = {
        "num_gamestates": iterations,
        "depth_explored": max_depth,
        "moves": sorted(move_summaries, key=lambda x: (x[2], -1.0 if x[1] is None else x[1]), reverse=True),
        "thinking_time": time.time() - start_time,
        "early_stop": False,
        "search_type": "graph_puct",
    }

    if verbose:
        print(f"graph_puct iterations: {iterations}")
        print(f"graph_puct depth: {max_depth}")
        print(f"graph_puct best move: {best_move}")
    return [best_move[0], best_move[1], move_metadata]
