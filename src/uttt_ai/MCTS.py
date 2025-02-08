import itertools
import copy
import time
import math
import gc

from utils import *
from Game import *


class SimulationTreeNode:
    def __init__(self, game, player):
        self.game = game
        self.player = player
        self.number_of_plays = 1
        self.children = {}
        self.total_score = 0
        self.depth_seen = 1
        self.unseen_children = list(game.legal_moves())
        # New tracking variables for adaptive thinking
        self.best_move_stable_count = 0
        self.last_best_move = None

    def get_score_of_move(self, m):
        if m not in self.children:
            print("{} is not a move from this state".format(m))
            return
        return float(self.children[m].total_score) / float(self.children[m].number_of_plays)

    def get_best_action_by_average_score(self):
        action = None
        best_score = -float("inf")
        for m, c in self.children.items():
            if c.total_score / float(c.number_of_plays) >= best_score:
                best_score = c.total_score / float(c.number_of_plays)
                action = m
        return action

    def get_best_action_and_confidence(self):
        """Returns best action and confidence based on score differential"""
        if not self.children:
            return None, 0

        moves_with_scores = []
        for m, c in self.children.items():
            avg_score = c.total_score / float(c.number_of_plays)
            moves_with_scores.append((m, avg_score))

        # Sort by score
        moves_with_scores.sort(key=lambda x: x[1], reverse=True)
        best_move = moves_with_scores[0][0]

        # Calculate confidence based on score differential
        confidence = 1.0
        if len(moves_with_scores) > 1:
            score_diff = moves_with_scores[0][1] - moves_with_scores[1][1]
            confidence = min(1.0, score_diff / 0.5)  # Normalize difference

        # Track move stability
        if best_move == self.last_best_move:
            self.best_move_stable_count += 1
        else:
            self.best_move_stable_count = 0
            self.last_best_move = best_move

        return best_move, confidence

    def best_predicted_line(self):
        line = []
        child = copy.deepcopy(self)
        while len(child.children) > 0:
            m = child.get_best_action_by_average_score()
            line.append((m[0], m[1], child.game.next_to_move))
            child = child.children[m]
        return line

    def get_best_action_by_ucb1(self, C=1):
        action = None
        best_score = -float("inf")
        for m, c in self.children.items():
            ucb = (c.total_score / float(c.number_of_plays)) + (
                        2 * C * math.sqrt(2 * math.log(self.number_of_plays) / float(c.number_of_plays)))
            if ucb >= best_score:
                best_score = ucb
                action = m
        return action

    def expand_one_child(self, game_path=[], opp_strat="greedy", comp_dist=[.5, .1, .05]):
        if len(self.unseen_children) == 0:
            print("no more unseen states from this node!")
            return

        m = self.unseen_children.pop()
        child_game = copy.deepcopy(self.game)
        child_game.make_move(m[0], m[1], child_game.next_to_move)

        if opp_strat.lower() == "mcts":
            if len(game_path) <= 1:
                s = comp_dist[0]
            elif (len(game_path) > 2) and (len(game_path) <= 4):
                s = comp_dist[1]
            else:
                s = comp_dist[2]
            n = evaluate_next_move(child_game, seconds_limit=s, node_limit=75, C=1, verbose=False)
            if n != None:
                child_game.make_move(n[0], n[1], child_game.next_to_move)
            gc.collect()
        else:
            child_game.run_n_greedy_moves(1)

        self.children[m] = SimulationTreeNode(child_game, self.player)
        score = self.children[m].game.board.score(self.player)
        self.children[m].total_score = score

        for node in game_path:
            node.number_of_plays += 1
            node.total_score += score
            if len(game_path) > node.depth_seen:
                node.depth_seen = len(game_path)

    def expand_tree_by_one(self, game_path=[], C=1, opp_strat="greedy", comp_dist=[.5, .1, .05]):
        if len(self.unseen_children) != 0:
            self.expand_one_child(game_path=game_path, opp_strat=opp_strat, comp_dist=comp_dist)
        else:
            if len(self.children) > 0:
                m = self.get_best_action_by_ucb1(C=C)
                self.children[m].expand_tree_by_one(game_path=game_path + [self], opp_strat=opp_strat)


def evaluate_next_move(game, seconds_limit=15, node_limit=float("inf"), C=1, opp_strat="greedy", verbose=True,
                       metadata=True):
    if (game.last_move == None) or (game.last_move[2] == "o"):
        next_to_move = "x"
    elif (game.last_move[2] == "x"):
        next_to_move = "o"
    else:
        print("last to move is invalid: {}".format(game.last_move[2]))

    node = SimulationTreeNode(game, game.next_to_move)

    # Set opponent strategy computation distribution
    comp_dist = []
    l = len(node.game.legal_moves())
    if seconds_limit <= 5:
        opp_strat = "greedy"
    elif (seconds_limit > 5) and (seconds_limit <= 10):
        if l >= 9:
            comp_dist = [.1, .05, .05]
        else:
            comp_dist = [.5, .1, .05]
    else:
        if l >= 9:
            comp_dist = [.1, .1, .05]
        elif l > 5:
            comp_dist = [.5, .1, .05]
        else:
            comp_dist = [1, .5, .1]

    # Set minimum exploration time based on position complexity
    min_time = min(3, seconds_limit * 0.2)  # At least 20% of max time or 3 seconds

    t = time.time()
    last_check_time = t
    check_interval = 0.5  # Check confidence every 0.5 seconds

    while (time.time() - t <= seconds_limit) and (node.number_of_plays < node_limit):
        node.expand_tree_by_one(C=C, opp_strat=opp_strat, comp_dist=comp_dist)

        # Check for early stopping every check_interval seconds
        current_time = time.time()
        if current_time - last_check_time >= check_interval:
            if current_time - t >= min_time:  # Only check after minimum time
                best_move, confidence = node.get_best_action_and_confidence()

                # Early stopping conditions:
                # 1. High confidence (>0.8) and stable best move for 3+ checks
                # 2. Moderate confidence (>0.6) and stable best move for 5+ checks
                # 3. Any confidence and stable best move for 8+ checks
                if ((confidence > 0.8 and node.best_move_stable_count >= 3) or
                        (confidence > 0.6 and node.best_move_stable_count >= 5) or
                        node.best_move_stable_count >= 8):
                    break

            last_check_time = current_time

    best_move = node.get_best_action_by_average_score()

    if metadata:
        move_metadata = {
            "num_gamestates": node.number_of_plays,
            "depth_explored": node.depth_seen,
            "moves": sorted([(m, node.get_score_of_move(m)) for m in node.children],
                            key=lambda x: x[1])[::-1],
            "predicted_line": node.best_predicted_line(),
            "thinking_time": time.time() - t,  # Add actual thinking time to metadata
            "early_stop": time.time() - t < seconds_limit  # Flag if we stopped early
        }

        if verbose:
            print("number of gamestates evaluated: {}".format(move_metadata["num_gamestates"]))
            print("depth of game tree explored: {}".format(move_metadata["depth_explored"]))
            print("best move for {}: {}".format(game.next_to_move, best_move))
            print("score of best move: {}".format(
                node.children[best_move].total_score / float(node.children[best_move].number_of_plays)))
            print("predicted line: {}".format(move_metadata["predicted_line"]))
            print("top moves:\n")
            for m, s in move_metadata["moves"]:
                print("\tmove: {}\tnum_plays: {}\tscore: {}".format(m, node.children[m].number_of_plays, s))

        return [best_move[0], best_move[1], move_metadata]
    return best_move