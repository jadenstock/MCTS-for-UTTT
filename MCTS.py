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
		self.player = player #we need to pass the player down through the sim
		self.number_of_plays = 1
		self.children = {}
		self.total_score = 0
		self.depth_seen = 1
		self.unseen_children = list(game.legal_moves()) #list of moves

	def get_score_of_move(self, m):
		if m not in self.children:
			print("{} is not a move from this state".format(m))
			return
		return float(self.children[m].total_score)/float(self.children[m].number_of_plays)

	def get_best_action_by_average_score(self):
		action = None
		best_score = -float("inf")
		for m, c in self.children.items():
			if c.total_score/float(c.number_of_plays) >= best_score:
				best_score = c.total_score/float(c.number_of_plays)
				action = m
		return action

	# fine the predicted line of moves, however deep the game tree goes.
	# This only gives our moves which is fine because we can construc opponent moves from those.
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
			#second factor in UCB1 socre is always less than 1 (before multiplication by 2C). We need to normalize average reward to [0,1]
			ucb = (c.total_score/float(c.number_of_plays)) + (2 * C * math.sqrt(2*math.log(self.number_of_plays)/float(c.number_of_plays)))
			if ucb >= best_score:
				best_score = ucb
				action = m
		return action
		
	#game path is a list of tree nodes
	#expand one unseen child from current game state
	#propigate score upp game path
	def expand_one_child(self, game_path=[], opp_strat="greedy", comp_dist=[.5, .1, .05]):
		if len(self.unseen_children)==0:
			print("no more unseen states from this node!")
			return

		m = self.unseen_children.pop()
		child_game = copy.deepcopy(self.game)
		#in order to evaluate the game we must make the move
		child_game.make_move(m[0], m[1], child_game.next_to_move)
		#now we anticipate what the opponent will do. Our base case way to do this is by assumping the opponent
		#chooses the next move to greedily optimize the score function. a more advanced way is to run a smaller mcts

		if opp_strat.lower()=="mcts":
			#decrease second_limit proportunal to game depth
			if len(game_path) <= 1:
				s = comp_dist[0]
			elif (len(game_path) > 2) and (len(game_path) <= 4):
				s = comp_dist[1]
			else:
				s = comp_dist[2]
			n = evaluate_next_move(child_game, seconds_limit=s, node_limit=75, C=1, verbose=False)
			# possible that we're at a node where there are no more moves and n is none. 
			if n != None:
				child_game.make_move(n[0], n[1], child_game.next_to_move)
			gc.collect()

		else:
			#this is the greedy case
			child_game.run_n_greedy_moves(1)

		#remember who the current player is in child node.
		self.children[m] = SimulationTreeNode(child_game, self.player)

		#score for current player
		score = self.children[m].game.board.score(self.player) 
		self.children[m].total_score = score
		
		#propigate through game_path
		for node in game_path:
			node.number_of_plays += 1
			node.total_score += score
			if len(game_path) > node.depth_seen:
				node.depth_seen = len(game_path)

	# traverse to leaf, then add new unseen nods, evaluate, propigate scores back through tree
	# every time we see a node that doesn't have all children looked at, expand all children immmediatly.
	def expand_tree_by_one(self, game_path=[], C=1, opp_strat="greedy", comp_dist=[.5, .1, .05]):
		if len(self.unseen_children) != 0:
			# we're at a terminal node, expand and propigate
			self.expand_one_child(game_path=game_path, opp_strat=opp_strat, comp_dist=comp_dist)
		else:
			if len(self.children) > 0:
				m = self.get_best_action_by_ucb1(C=C)
				self.children[m].expand_tree_by_one(game_path=game_path+[self], opp_strat=opp_strat)
			#else: no unseen children and no seen children, i.e. the game is over. do nothing? what happens here

# returns a move tuple m. m[0] is chosen board, m[1] is chosen cell. optional flag m[2] will have move_metadata
# opp strategy can either be mcts ot greedy. if mcts then run a smaller mcts tree for each opp move.
def evaluate_next_move(game, seconds_limit=15, node_limit=float("inf"), C=1, opp_strat="greedy", verbose=True, metadata=True):
	if (game.last_move == None) or (game.last_move[2] == "o"):
		next_to_move = "x"
	elif (game.last_move[2] == "x"):
		next_to_move = "o"
	else:
		print("last to move is invalid: {}".format(game.last_move[2]))

	node = SimulationTreeNode(game, game.next_to_move)

	#if we have more than 9 move options give extra few seconds of compute?

	#thinking_time = 3
	#predicted_moves = []

	comp_dist = []
	l = len(node.game.legal_moves())
	if seconds_limit <= 5:
		opp_strat = "greedy"
	elif (seconds_limit > 5) and (seconds_limit<=10):
		if l >= 9:
			comp_dist=[.1, .05, .05]
		else:
			comp_dist=[.5, .1, .05]
	else:
		if l >= 9:
			comp_dist=[.1, .1, .05]
		elif l > 5:
			comp_dist=[.5, .1, .05]
		else:
			comp_dist=[1, .5, .1]
	
	#while time limit isn't reached keep expanding nodes or node_limit reached

	t = time.time()
	while (((time.time() - t) <= seconds_limit) and (node.number_of_plays < node_limit)):

		#if (time.time()-t) > thinking_time:
		#	predicted_moves.append((thinking_time, node.get_best_action_by_average_score()))
		#	thinking_time += 2

		node.expand_tree_by_one(C=C, opp_strat=opp_strat, comp_dist=comp_dist)

	best_move = node.get_best_action_by_average_score()

	if metadata:
		move_metadata = {}
		move_metadata["num_gamestates"] = node.number_of_plays
		move_metadata["depth_explored"] = node.depth_seen
		move_metadata["moves"] = sorted([(m, node.get_score_of_move(m)) for m in node.children], key = lambda x:x[1])[::-1]
		move_metadata["predicted_line"] = node.best_predicted_line()

	if verbose:
		move_metadata = {}
		move_metadata["num_gamestates"] = node.number_of_plays
		move_metadata["depth_explored"] = node.depth_seen
		move_metadata["moves"] = sorted([(m, node.get_score_of_move(m)) for m in node.children], key = lambda x:x[1])[::-1]
		move_metadata["predicted_line"] = node.best_predicted_line()
		print("number of gamestates evaluated: {}".format(move_metadata["num_gamestates"]))
		print("depth of game tree explored: {}".format(move_metadata["depth_explored"]))
		print("best move for {}: {}".format(game.next_to_move, best_move))
		print("score of best move: {}".format(node.children[best_move].total_score/float(node.children[best_move].number_of_plays)))
		print("predicted line: {}").format(move_metadata["predicted_line"])
		#print("progression of move choices: {}".format(predicted_moves))
		print("top moves:\n")
		for m,s in move_metadata["moves"]:
			print("\tmove: {}\tnum_plays: {}\tscore: {}".format(m, node.children[m].number_of_plays, s))

	if metadata:
		return [best_move[0], best_move[1], move_metadata]
	return best_move



