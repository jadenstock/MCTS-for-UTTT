from bots.baseline_mcts.eval import LINES, evaluate_game_state as baseline_evaluate_game_state, score_local_board


def _count_open_twos(cells, player):
    opponent = "o" if player == "x" else "x"
    count = 0
    for line in LINES:
        segment = [cells[i] for i in line]
        if segment.count(player) == 2 and segment.count(opponent) == 0 and segment.count("") == 1:
            count += 1
    return count


def evaluate_game_state(board, player, config):
    base_score = baseline_evaluate_game_state(board, player, config)
    opponent = "o" if player == "x" else "x"
    if board.winner in (player, opponent, "draw"):
        return base_score

    player_won_boards = sum(1 for mini_board in board.boards if mini_board.winner == player)
    opponent_won_boards = sum(1 for mini_board in board.boards if mini_board.winner == opponent)

    won_board_delta = (player_won_boards - opponent_won_boards) / 9.0
    won_board_bonus = float(config.get("won_board_bonus", 0.0)) * won_board_delta

    open_two_bonus_weight = float(config.get("open_two_bonus", 0.0))
    open_two_delta = 0.0
    for mini_board in board.boards:
        if mini_board.winner != "":
            continue
        open_two_delta += _count_open_twos(mini_board.cells, player)
        open_two_delta -= _count_open_twos(mini_board.cells, opponent)
    open_two_bonus = open_two_bonus_weight * (open_two_delta / 18.0)

    return max(0.0, min(1.0, base_score + won_board_bonus + open_two_bonus))


def score_local(board, player, config):
    return score_local_board(board, player, config)
