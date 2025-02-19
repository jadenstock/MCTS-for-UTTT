import copy
import time
import math

from config import *

class SimulationTreeNode:
    def __init__(self, game, player):
        self.game = game
        self.player = player
        self.number_of_plays = 1
        self.children = {}
        self.total_score = 0
        self.depth_seen = 1
        self.unseen_children = list(game.legal_moves())
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

        moves_with_scores.sort(key=lambda x: x[1], reverse=True)
        best_move = moves_with_scores[0][0]

        confidence = 1.0
        if len(moves_with_scores) > 1:
            score_diff = moves_with_scores[0][1] - moves_with_scores[1][1]
            confidence = min(1.0, score_diff / SCORE_DIFF_NORMALIZER)

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

    def get_best_action_by_ucb1(self, C):
        """Pure UCB1 implementation with externally controlled constant"""
        action = None
        best_score = -float("inf")
        for m, c in self.children.items():
            ucb = (c.total_score / float(c.number_of_plays)) + (
                    2 * C * math.sqrt(2 * math.log(self.number_of_plays) / float(c.number_of_plays)))
            if ucb >= best_score:
                best_score = ucb
                action = m
        return action

    def expand_one_child(self, game_path=[], opp_strat="greedy", comp_dist=COMP_DIST_MEDIUM_MOVES):
        if len(self.unseen_children) == 0:
            print("no more unseen states from this node!")
            return

        m = self.unseen_children.pop()
        child_game = copy.deepcopy(self.game)
        child_game.make_move(m[0], m[1], child_game.next_to_move)

        # Create the child node with initial game state
        self.children[m] = SimulationTreeNode(child_game, self.player)

        # Create a separate game for simulation
        simulation_game = copy.deepcopy(child_game)

        # Simulate until game is over
        while simulation_game.board.winner == "" and len(simulation_game.legal_moves()) > 0:
            simulation_game.run_n_greedy_moves(1)

        # Score the terminal state
        score = simulation_game.board.score(self.player)
        self.children[m].total_score = score

        # Backpropagate the result
        for node in game_path:
            node.number_of_plays += 1
            node.total_score += score
            if len(game_path) > node.depth_seen:
                node.depth_seen = len(game_path)

    def expand_tree_by_one(self, game_path=[], C=DEFAULT_UCB_CONSTANT, opp_strat="greedy",
                           comp_dist=COMP_DIST_MEDIUM_MOVES):
        if len(self.unseen_children) != 0:
            self.expand_one_child(game_path=game_path, opp_strat=opp_strat, comp_dist=comp_dist)
        else:
            if len(self.children) > 0:
                m = self.get_best_action_by_ucb1(C)
                self.children[m].expand_tree_by_one(game_path=game_path + [self], opp_strat=opp_strat)


def calculate_ucb_constant(elapsed_time, total_time, num_moves, base_constant=DEFAULT_UCB_CONSTANT):
    """Calculate dynamic UCB constant based on search progress and position complexity"""
    # Time-based scaling - explore more early, exploit more later
    time_ratio = elapsed_time / total_time
    time_factor = 1.0 + (1.0 - time_ratio)  # Starts at 2.0, ends at 1.0

    # Branching factor scaling - explore more in complex positions
    branching_factor = min(1.0 + (num_moves / 20.0), 2.0)  # Cap at 2x

    return base_constant * time_factor * branching_factor


def evaluate_next_move(game, seconds_limit=DEFAULT_SECONDS_LIMIT, node_limit=DEFAULT_NODE_LIMIT,
                       C=DEFAULT_UCB_CONSTANT, opp_strat="greedy", force_full_time=False, verbose=True, metadata=True):
    node = SimulationTreeNode(game, game.next_to_move)

    # Set opponent strategy computation distribution
    l = len(node.game.legal_moves())
    if seconds_limit <= GREEDY_TIME_THRESHOLD:
        opp_strat = "greedy"
        comp_dist = COMP_DIST_MEDIUM_MOVES
    elif seconds_limit <= MEDIUM_TIME_THRESHOLD:
        if l >= COMPLEX_POSITION_THRESHOLD:
            comp_dist = COMP_DIST_MANY_MOVES
        else:
            comp_dist = COMP_DIST_MEDIUM_MOVES
    else:
        if l >= COMPLEX_POSITION_THRESHOLD:
            comp_dist = COMP_DIST_MANY_MOVES
        elif l > MEDIUM_POSITION_THRESHOLD:
            comp_dist = COMP_DIST_MEDIUM_MOVES
        else:
            comp_dist = COMP_DIST_FEW_MOVES

    min_time = min(3, seconds_limit * MIN_TIME_RATIO)
    start_time = time.time()
    last_check_time = start_time

    while (time.time() - start_time <= seconds_limit) and (node.number_of_plays < node_limit):
        # Calculate dynamic UCB constant
        elapsed_time = time.time() - start_time
        dynamic_C = calculate_ucb_constant(elapsed_time, seconds_limit, l, C)

        node.expand_tree_by_one(C=dynamic_C, opp_strat=opp_strat, comp_dist=comp_dist)

        if not force_full_time:
            current_time = time.time()
            if current_time - last_check_time >= CHECK_INTERVAL:
                if current_time - start_time >= min_time:
                    best_move, confidence = node.get_best_action_and_confidence()

                    if ((confidence > CONFIDENCE_HIGH and node.best_move_stable_count >= STABLE_CHECKS_HIGH) or
                            (
                                    confidence > CONFIDENCE_MODERATE and node.best_move_stable_count >= STABLE_CHECKS_MODERATE) or
                            node.best_move_stable_count >= STABLE_CHECKS_LOW):
                        break

                last_check_time = current_time

    best_move = node.get_best_action_by_average_score()

    if metadata:
        move_metadata = {
            "num_gamestates": node.number_of_plays,
            "depth_explored": node.depth_seen,
            "moves": sorted([(m, node.get_score_of_move(m)) for m in node.children],
                            key=lambda x: x[1])[::-1],
            "thinking_time": time.time() - start_time,
            "early_stop": not force_full_time and time.time() - start_time < seconds_limit
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