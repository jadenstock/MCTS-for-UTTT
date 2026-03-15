from dataclasses import dataclass


@dataclass
class ExactSearchStats:
    nodes_evaluated: int = 0
    cache_hits: int = 0
    max_depth: int = 0


def count_empty_cells(game):
    return sum(cell == "" for board in game.board.boards for cell in board.cells)


def _state_key(game):
    last_cell = game.move_stack[-1][1] if game.move_stack else -1
    boards = tuple(tuple(mini.cells) for mini in game.board.boards)
    winners = tuple(mini.winner for mini in game.board.boards)
    return (boards, winners, game.board.winner, game.next_to_move, last_cell)


def _terminal_value(game, root_player):
    if game.board.winner == root_player:
        return 1.0
    opponent = "o" if root_player == "x" else "x"
    if game.board.winner == opponent:
        return 0.0
    legal = game.legal_moves()
    if not legal:
        return 0.5
    return None


def _solve_value(game, root_player, cache, stats, depth, alpha, beta):
    stats.nodes_evaluated += 1
    if depth > stats.max_depth:
        stats.max_depth = depth

    terminal = _terminal_value(game, root_player)
    if terminal is not None:
        return terminal

    key = _state_key(game)
    cached = cache.get(key)
    if cached is not None:
        stats.cache_hits += 1
        return cached

    legal = game.legal_moves()
    maximizing = game.next_to_move == root_player
    if maximizing:
        value = -1.0
        for move in legal:
            game.make_move(move[0], move[1], game.next_to_move)
            child = _solve_value(game, root_player, cache, stats, depth + 1, alpha, beta)
            game.undo_last_move()
            if child > value:
                value = child
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
    else:
        value = 2.0
        for move in legal:
            game.make_move(move[0], move[1], game.next_to_move)
            child = _solve_value(game, root_player, cache, stats, depth + 1, alpha, beta)
            game.undo_last_move()
            if child < value:
                value = child
            if value < beta:
                beta = value
            if alpha >= beta:
                break

    cache[key] = value
    return value


def solve_root_exact(game, root_player=None):
    player = root_player or game.next_to_move
    legal = game.legal_moves()
    if not legal:
        return None, {}, ExactSearchStats()
    if len(legal) == 1:
        move = legal[0]
        game.make_move(move[0], move[1], game.next_to_move)
        score = _terminal_value(game, player)
        if score is None:
            score = 0.5
        game.undo_last_move()
        return move, {move: score}, ExactSearchStats(nodes_evaluated=1, max_depth=1)

    cache = {}
    stats = ExactSearchStats()
    move_values = {}
    best_move = None
    best_value = -1.0

    for move in legal:
        game.make_move(move[0], move[1], game.next_to_move)
        value = _solve_value(game, player, cache, stats, 1, 0.0, 1.0)
        game.undo_last_move()
        move_values[move] = value
        key = (value, -move[0], -move[1])
        if best_move is None:
            best_move = move
            best_value = value
        else:
            best_key = (best_value, -best_move[0], -best_move[1])
            if key > best_key:
                best_move = move
                best_value = value

    return best_move, move_values, stats
