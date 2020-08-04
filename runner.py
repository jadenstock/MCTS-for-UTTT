#import flask
from flask import Flask, request, redirect, url_for, flash, jsonify
import json

from utils import *
from Game import *
from MCTS import *

def run_game(bot_player="x", num_seconds=5):
	g = Game()
	bot_player = bot_player

	while g.board.winner == "":
		print("\n{} to move\n".format(g.next_to_move))
		print(g)
		print("\n")

		if g.next_to_move == "o":
			m = evaluate_next_move(g, seconds_limit=15, C=1, opp_strat='mcts')
			g.make_move(m[0], m[1], g.next_to_move)
			gc.collect()
			continue

		#50C beat 500C, try with timing experiments. Also try on Amazon.
		if (g.last_move == None) or (g.board.boards[g.last_move[1]].winner != ""):
			b = int(raw_input("what board would you like to place on?\t"))
			c = int(raw_input("what cell would you like to place on?\t"))
			g.make_move(b-1, c-1, g.next_to_move)
		else:
			print("you must place in board {}".format(g.last_move[1]+1))
			c = int(raw_input("what cell would you like to place on?\t"))
			g.make_move(g.last_move[1], c-1, g.next_to_move)

	print("{} won the game!".format(g.board.winner))


if __name__ == '__main__':
	run_game()

	# idea: adaptive thinking time. some moves are so obvious it doesn't need to think much. just watch score of first choice and second choice.
	# other times it's a hard choice and thinking more does better. maybe just compute until it's sure?

	# idea: use group training or self play to find best hyperparams. Specifically make the score function something that's passed in 
	# then have a tournament among bots with different score functions to see which performs best

	# find ways to prune search tree? (this can be dangerous. Often best to just leave more choices for bot)
	
	# run experiment over how it changes optimal moves with more thinking time. are there hidden moves it takes awhile to find?

	# come up with perplexity score for player. how well did it predict their moves? can come up with actual probability dist of moves.

	# biggest idea: Find way to make it probabilistic. Right now when a node is added to the tree the algorithm comes up with an opponent move
	# and then it goes further into the game tree. But what if the opponent doesn't make that move? then that whole branch isn't great. Would be better
	# to use some sort of expected opponent move as is done in UCT+ in Monte-Carlo Tree Search in Poker using Expected Reward Distributions
	# (http://web.cs.ucla.edu/~guyvdb/papers/VdBACML09.pdf). Idea use current approach to come up with opponent move model (i.e. they are 80% liekly to play here, 15% there, 5% etc.)
	# then have them play those moves randomly or something and propigate average scores back up? Anyway surely there is more research on this because it seems like a pretty
	# fundimental problem with MCTS. 
