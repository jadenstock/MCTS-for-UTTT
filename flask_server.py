#import flask
from flask import Flask, request, redirect, url_for, flash, jsonify
import flask_cors
import json
import ast

from utils import *
from Game import *
from MCTS import *

app = Flask(__name__)
@app.route('/api/makemove/', methods=['POST', 'OPTIONS'])
@flask_cors.cross_origin()
def make_move():
	jsonfile = request.get_json()

	# not really sure why I need two literal evals here
	data = ast.literal_eval(json.dumps(jsonfile))
	data = ast.literal_eval(data)

	g = make_game(data["game_board"], [int(data["last_move"][0]), int(data["last_move"][1]), data["last_move"][2].lower()])
	m = evaluate_next_move(g, seconds_limit=int(data["compute_time"]), verbose=False)

	res = {"board":m[0], "cell":m[1], "metadata":m[2]}
	return jsonify(res)

if __name__ == '__main__':
	app.run(debug=True)