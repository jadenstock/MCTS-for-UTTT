LINES = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6],
]


def _normalize_token(token):
    return token.lower() if isinstance(token, str) else token


def _normalize_board(board):
    return [_normalize_token(cell) for cell in board]


def score_local_board(board, player, config):
    board = _normalize_board(board)
    player = _normalize_token(player)
    opponent = "o" if player == "x" else "x"

    base_potential = float(config.get("base_potential", 0.15))
    line_exponent = float(config.get("line_exponent", 1.5))
    max_multiplier = float(config.get("max_multiplier", 1.5))
    weight_best = float(config.get("weight_best", 0.6))
    weight_path = float(config.get("weight_path", 0.4))
    max_score = float(config.get("max_score", 0.9))

    line_potentials = []
    for line in LINES:
        cells = [board[i] for i in line]
        player_count = cells.count(player)
        opponent_count = cells.count(opponent)

        if player_count == 3:
            return 1.0
        if opponent_count == 3:
            return 0.0
        if player_count > 0 and opponent_count > 0:
            continue
        if opponent_count == 0:
            potential = base_potential + ((player_count / 3) ** line_exponent)
            line_potentials.append(potential)

    if not line_potentials:
        return 0.0

    best_line = max(line_potentials)
    num_paths = len(line_potentials)
    path_synergy = sum(sorted(line_potentials, reverse=True)[:4]) / 4
    path_multiplier = min(max_multiplier, 1 + (num_paths / 8))
    path_strength = path_synergy * path_multiplier

    score = weight_best * best_line + weight_path * path_strength
    return min(max_score, score)


def calculate_square_importance(board, config):
    board = _normalize_board(board)
    importance_win_weight = float(config.get("importance_win_weight", 2.0))
    importance_develop_weight = float(config.get("importance_develop_weight", 0.3))
    importance_fresh_weight = float(config.get("importance_fresh_weight", 0.1))

    def count_viable_paths(player):
        opponent = "o" if player == "x" else "x"
        viable_paths = 0
        for line in LINES:
            cells = [board[i] for i in line]
            if opponent not in cells:
                viable_paths += 1
        return viable_paths

    importance_x = [0.0] * 9
    importance_o = [0.0] * 9
    viable_x = count_viable_paths("x")
    viable_o = count_viable_paths("o")

    for line in LINES:
        cells = [board[i] for i in line]
        empty_indices = [i for i in line if board[i] == ""]
        if cells.count("x") == 3 or cells.count("o") == 3:
            return [0.0] * 9, [0.0] * 9
        if not empty_indices:
            continue

        x_count = cells.count("x")
        o_count = cells.count("o")
        if viable_x == 0:
            imp_x_line = 0.0
        elif o_count > 0:
            imp_x_line = 0.0
        elif x_count == 2:
            imp_x_line = min(1.0, importance_win_weight / viable_x)
        elif x_count == 1:
            imp_x_line = importance_develop_weight / viable_x
        else:
            imp_x_line = importance_fresh_weight / viable_x

        if viable_o == 0:
            imp_o_line = 0.0
        elif x_count > 0:
            imp_o_line = 0.0
        elif o_count == 2:
            imp_o_line = min(1.0, importance_win_weight / viable_o)
        elif o_count == 1:
            imp_o_line = importance_develop_weight / viable_o
        else:
            imp_o_line = importance_fresh_weight / viable_o

        for idx in empty_indices:
            importance_x[idx] += imp_x_line
            importance_o[idx] += imp_o_line

    max_x = max(importance_x) if max(importance_x) > 0 else 1
    max_o = max(importance_o) if max(importance_o) > 0 else 1
    importance_x = [min(1.0, score / max_x) for score in importance_x]
    importance_o = [min(1.0, score / max_o) for score in importance_o]
    return importance_x, importance_o


def evaluate_game_state(board, player, config):
    opponent = "o" if player == "x" else "x"
    draw_value = float(config.get("terminal_draw_value", 0.5))
    if board.winner == player:
        return 1.0
    if board.winner == opponent:
        return 0.0
    if board.winner == "draw":
        return draw_value

    has_playable_cells = any(
        mini_board.winner == "" and any(cell == "" for cell in mini_board.cells)
        for mini_board in board.boards
    )
    if (not has_playable_cells) or (hasattr(board, "has_viable_big_board_line") and not board.has_viable_big_board_line()):
        return draw_value

    global_score_weight = float(config.get("global_score_weight", 0.65))
    strategic_score_weight = float(config.get("strategic_score_weight", 0.35))
    offensive_weight = float(config.get("offensive_weight", 0.7))
    defensive_weight = float(config.get("defensive_weight", 0.3))
    final_max_score = float(config.get("final_max_score", 0.9))

    global_board = [b.winner for b in board.boards]
    global_importance_player, global_importance_opp = calculate_square_importance(global_board, config)
    global_score = score_local_board(global_board, player, config)

    strategic_score = 0.0
    total_weight = 0.0
    for i, mini_board in enumerate(board.boards):
        if mini_board.winner != "":
            continue
        winnability_player = score_local_board(mini_board.cells, player, config)
        winnability_opp = score_local_board(mini_board.cells, opponent, config)
        board_importance = max(global_importance_player[i], global_importance_opp[i])
        board_score = (
            offensive_weight * winnability_player * global_importance_player[i]
            - defensive_weight * winnability_opp * global_importance_opp[i]
        )
        strategic_score += board_score * board_importance
        total_weight += board_importance

    if total_weight > 0:
        strategic_score = (strategic_score / total_weight + 1) / 2
    else:
        strategic_score = 0.0

    final_score = global_score_weight * global_score + strategic_score_weight * strategic_score
    return max(0.0, min(final_max_score, final_score))
