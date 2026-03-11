#!/usr/bin/env python
import argparse
import random
from dataclasses import dataclass

from ai.mcts import evaluate_next_move
from core.game import Game


@dataclass
class BenchmarkResult:
    games: int
    x_wins: int
    o_wins: int
    draws: int
    avg_moves: float


def _apply_opening_noise(game, opening_random_plies, rng):
    for _ in range(opening_random_plies):
        legal = game.legal_moves()
        if not legal or game.board.winner:
            break
        move = rng.choice(legal)
        game.make_move(move[0], move[1], game.next_to_move)


def _play_game(agent_x, agent_o, compute_time, node_limit, opening_random_plies, seed):
    rng = random.Random(seed)
    game = Game()
    _apply_opening_noise(game, opening_random_plies, rng)

    while not game.board.winner and game.legal_moves():
        current_agent = agent_x if game.next_to_move == "x" else agent_o
        move = evaluate_next_move(
            game,
            agent_id=current_agent,
            seconds_limit=compute_time,
            node_limit=node_limit,
            verbose=False,
            metadata=False,
        )
        if move is None:
            break
        game.make_move(move[0], move[1], game.next_to_move)

    if game.board.winner == "x":
        return "x", len(game.move_stack)
    if game.board.winner == "o":
        return "o", len(game.move_stack)
    return "draw", len(game.move_stack)


def run_benchmark(agent_a, agent_b, games, compute_time, node_limit, opening_random_plies, seed):
    # agent_a plays first on even games, second on odd games.
    x_wins = 0
    o_wins = 0
    draws = 0
    total_moves = 0

    for idx in range(games):
        if idx % 2 == 0:
            agent_x, agent_o = agent_a, agent_b
            a_is_x = True
        else:
            agent_x, agent_o = agent_b, agent_a
            a_is_x = False

        winner, move_count = _play_game(
            agent_x=agent_x,
            agent_o=agent_o,
            compute_time=compute_time,
            node_limit=node_limit,
            opening_random_plies=opening_random_plies,
            seed=seed + idx,
        )
        total_moves += move_count

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
    args = parser.parse_args()

    result = run_benchmark(
        agent_a=args.agent_a,
        agent_b=args.agent_b,
        games=args.games,
        compute_time=args.compute_time,
        node_limit=args.node_limit,
        opening_random_plies=args.opening_random_plies,
        seed=args.seed,
    )

    print("\n=== Benchmark Summary ===")
    print(f"games: {result.games}")
    print(f"x_wins: {result.x_wins}")
    print(f"o_wins: {result.o_wins}")
    print(f"draws: {result.draws}")
    print(f"avg_moves: {result.avg_moves:.2f}")


if __name__ == "__main__":
    main()
