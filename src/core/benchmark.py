#!/usr/bin/env python
import argparse
import json
import random
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

from ai.mcts import evaluate_next_move
from core.game import Game
from utils.game_storage import GameStorage


@dataclass
class BenchmarkResult:
    games: int
    x_wins: int
    o_wins: int
    draws: int
    avg_moves: float


def _apply_opening_noise(game, opening_random_plies, rng, storage=None, game_id=None):
    for _ in range(opening_random_plies):
        legal = game.legal_moves()
        if not legal or game.board.winner:
            break
        move = rng.choice(legal)
        game.make_move(move[0], move[1], game.next_to_move)
        if storage is not None and game_id is not None:
            storage.save_game(game_id, game, {"opening_noise": True})


def _play_game(
    agent_x,
    agent_o,
    compute_time,
    node_limit,
    opening_random_plies,
    seed,
    storage=None,
    game_id=None,
    capture_metadata=False,
):
    rng = random.Random(seed)
    game = Game()
    _apply_opening_noise(game, opening_random_plies, rng, storage=storage, game_id=game_id)

    while not game.board.winner and game.legal_moves():
        current_agent = agent_x if game.next_to_move == "x" else agent_o
        move = evaluate_next_move(
            game,
            agent_id=current_agent,
            seconds_limit=compute_time,
            node_limit=node_limit,
            verbose=False,
            metadata=capture_metadata,
        )
        if move is None:
            break
        if capture_metadata:
            board_idx, cell_idx, move_metadata = move
        else:
            board_idx, cell_idx = move
            move_metadata = None
        game.make_move(board_idx, cell_idx, game.next_to_move)
        if storage is not None and game_id is not None:
            storage.save_game(game_id, game, move_metadata)

    if game.board.winner == "x":
        return "x", len(game.move_stack)
    if game.board.winner == "o":
        return "o", len(game.move_stack)
    return "draw", len(game.move_stack)


def _annotate_saved_game(save_dir, game_id, context):
    path = Path(save_dir) / f"{game_id}.json"
    if not path.exists():
        return
    with open(path) as f:
        data = json.load(f)
    data["benchmark_context"] = context
    temp_path = path.with_suffix(".tmp")
    with open(temp_path, "w") as f:
        json.dump(data, f)
    temp_path.replace(path)


def run_benchmark(
    agent_a,
    agent_b,
    games,
    compute_time,
    node_limit,
    opening_random_plies,
    seed,
    save_games=False,
    save_dir="data/benchmark_games",
    save_metadata=False,
):
    # agent_a plays first on even games, second on odd games.
    x_wins = 0
    o_wins = 0
    draws = 0
    total_moves = 0
    storage = GameStorage(data_dir=save_dir) if save_games else None
    session_tag = datetime.now().strftime("%Y%m%d_%H%M%S")

    for idx in range(games):
        if idx % 2 == 0:
            agent_x, agent_o = agent_a, agent_b
            a_is_x = True
        else:
            agent_x, agent_o = agent_b, agent_a
            a_is_x = False

        game_id = (
            f"bench_{session_tag}_g{idx+1}_{agent_x}_vs_{agent_o}_seed{seed+idx}"
            if save_games
            else None
        )

        winner, move_count = _play_game(
            agent_x=agent_x,
            agent_o=agent_o,
            compute_time=compute_time,
            node_limit=node_limit,
            opening_random_plies=opening_random_plies,
            seed=seed + idx,
            storage=storage,
            game_id=game_id,
            capture_metadata=save_metadata,
        )
        total_moves += move_count
        if save_games and game_id:
            _annotate_saved_game(
                save_dir=save_dir,
                game_id=game_id,
                context={
                    "agent_a": agent_a,
                    "agent_b": agent_b,
                    "agent_x": agent_x,
                    "agent_o": agent_o,
                    "game_index": idx + 1,
                    "seed": seed + idx,
                    "compute_time": compute_time,
                    "node_limit": node_limit,
                    "opening_random_plies": opening_random_plies,
                },
            )

        if winner == "x":
            x_wins += 1
        elif winner == "o":
            o_wins += 1
        else:
            draws += 1

        # per-agent report for each game
        if winner == "draw":
            result = "draw"
        elif (winner == "x" and a_is_x) or (winner == "o" and not a_is_x):
            result = "agent_a_win"
        else:
            result = "agent_b_win"

        print(f"game={idx+1}/{games} winner={winner} result={result} moves={move_count}")

    return BenchmarkResult(
        games=games,
        x_wins=x_wins,
        o_wins=o_wins,
        draws=draws,
        avg_moves=(total_moves / games) if games else 0.0,
    )


def main():
    parser = argparse.ArgumentParser(description="Benchmark two UTTT agents with reproducible self-play.")
    parser.add_argument("--agent-a", default="default", help="Agent id for player A")
    parser.add_argument("--agent-b", default="aggressive", help="Agent id for player B")
    parser.add_argument("--games", type=int, default=20, help="Number of games")
    parser.add_argument("--compute-time", type=int, default=60, help="Seconds per move ceiling")
    parser.add_argument("--node-limit", type=int, default=750, help="Node expansions per move")
    parser.add_argument("--opening-random-plies", type=int, default=2, help="Random opening plies per game")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed")
    parser.add_argument("--save-games", action="store_true", help="Persist every benchmark game for analysis")
    parser.add_argument("--save-dir", default="data/bot_games", help="Directory for saved benchmark games")
    parser.add_argument("--save-metadata", action="store_true", help="Save per-move search metadata")
    args = parser.parse_args()

    result = run_benchmark(
        agent_a=args.agent_a,
        agent_b=args.agent_b,
        games=args.games,
        compute_time=args.compute_time,
        node_limit=args.node_limit,
        opening_random_plies=args.opening_random_plies,
        seed=args.seed,
        save_games=args.save_games,
        save_dir=args.save_dir,
        save_metadata=args.save_metadata,
    )

    print("\n=== Benchmark Summary ===")
    print(f"games: {result.games}")
    print(f"x_wins: {result.x_wins}")
    print(f"o_wins: {result.o_wins}")
    print(f"draws: {result.draws}")
    print(f"avg_moves: {result.avg_moves:.2f}")


if __name__ == "__main__":
    main()
