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