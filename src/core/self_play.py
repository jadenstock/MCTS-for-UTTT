#!/usr/bin/env python
import argparse
import json
import time
import os
import sys
from core.game import Game  # Adjust the import if necessary
from ai.mcts import evaluate_next_move
from utils.game_storage import GameStorage


def run_self_play(agent1, agent2, compute_time):
    """
    Run a self-play game between two agents.

    Args:
        agent1 (str): Agent id for player "x" (first mover).
        agent2 (str): Agent id for player "o".
        compute_time (int): Seconds limit per move.

    Returns:
        tuple: (game instance, move log)
    """
    game = Game()
    moves_log = []
    move_count = 0
    print(f"Starting self-play game: Agent 'x' = {agent1}, Agent 'o' = {agent2}")

    # Game loop: play until the game is over (win or draw)
    while not game.board.winner and game.legal_moves():
        sys.stdout.flush()
        move_count += 1
        current_agent = agent1 if game.next_to_move == "x" else agent2
        print(f"\nMove {move_count}: Player {game.next_to_move} using agent '{current_agent}'")

        # Evaluate the next move for the current agent.
        move = evaluate_next_move(game, seconds_limit=compute_time, verbose=False, agent_id=current_agent)
        board_idx, cell_idx, metadata = move
        print(f"Chosen move: Board {board_idx}, Cell {cell_idx}")

        # Make the move on the game.
        if not game.make_move(board_idx, cell_idx, game.next_to_move):
            print("Encountered an illegal move; terminating simulation.")
            break

        # Append move to the game stack and log.
        game.move_stack.append((board_idx, cell_idx, game.next_to_move))
        moves_log.append({
            "player": game.next_to_move,
            "move": {"board": board_idx, "cell": cell_idx},
            "metadata": metadata
        })

        # Print a summary of the board state.
        if move_count % 3 == 0:
            print(f"After move {move_count}, board state:")
            print(str(game))

    # Determine the game result.
    if game.board.winner:
        result = f"{game.board.winner} wins"
    else:
        result = "draw"

    print("\nFinal Game Result:", result)

    # Save the game into a self-play directory.
    self_play_dir = "data/self_play_games"
    if not os.path.exists(self_play_dir):
        os.makedirs(self_play_dir)

    # Initialize GameStorage with the self-play directory.
    storage = GameStorage(data_dir=self_play_dir)
    # Generate a unique game ID, e.g., based on timestamp.
    game_id = f"selfplay_{int(time.time())}"
    storage.save_game(game_id, game, moves_log)
    print(f"Game saved with id: {game_id} in directory: {self_play_dir}")

    return game, moves_log


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a self-play game between two agents")
    parser.add_argument("--agent1", type=str, default="default", help="Agent ID for player 'x'")
    parser.add_argument("--agent2", type=str, default="default", help="Agent ID for player 'o'")
    parser.add_argument("--compute_time", type=int, default=5, help="Compute time per move in seconds")
    args = parser.parse_args()

    run_self_play(args.agent1, args.agent2, args.compute_time)
