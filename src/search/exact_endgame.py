from dataclasses import dataclass
import time


@dataclass
class ExactSearchStats:
    nodes_evaluated: int = 0
    cache_hits: int = 0
    max_depth: int = 0
    truncated: bool = False


def count_empty_cells(game):
    return sum(cell == "" for board in game.board.boards for cell in board.cells)


def count_legal_moves(game):
    return len(game.legal_moves())


def count_legal_cells(game):
    """
    Count empty cells in mini-boards that are still legally relevant
    (i.e. mini-board winner is unset). Empty cells in already won/drawn
    mini-boards are ignored.
    """
    total = 0
    for mini in game.board.boards:
        if mini.winner != "":
            continue
        total += sum(cell == "" for cell in mini.cells)
    return total


def _state_key(game):
    last_cell = game.move_stack[-1][1] if game.move_stack else -1
    boards = tuple(tuple(mini.cells) for mini in game.board.boards)
    winners = tuple(mini.winner for mini in game.board.boards)
    return (boards, winners, game.board.winner, game.next_to_move, last_cell)


def _terminal_value(game, root_player, draw_value=0.5):
    if game.board.winner == root_player:
        return 1.0
    opponent = "o" if root_player == "x" else "x"
    if game.board.winner == opponent:
        return 0.0
    legal = game.legal_moves()
    if not legal:
        return float(draw_value)
    return None


def _limits_hit(stats, start_time, max_nodes, max_seconds):
    if max_nodes and max_nodes > 0 and stats.nodes_evaluated >= int(max_nodes):
        return True
    if max_seconds and max_seconds > 0 and (time.time() - start_time) >= float(max_seconds):
        return True
    return False


def _solve_value(
    game,
    root_player,
    cache,
    stats,
    depth,
    alpha,
    beta,
    draw_value=0.5,
    start_time=None,
    max_nodes=0,
    max_seconds=0.0,
):
    if _limits_hit(stats, start_time, max_nodes, max_seconds):
        stats.truncated = True
        return None
    stats.nodes_evaluated += 1
    if depth > stats.max_depth:
        stats.max_depth = depth

    terminal = _terminal_value(game, root_player, draw_value=draw_value)
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
            child = _solve_value(
                game,
                root_player,
                cache,
                stats,
                depth + 1,
                alpha,
                beta,
                draw_value=draw_value,
                start_time=start_time,
                max_nodes=max_nodes,
                max_seconds=max_seconds,
            )
            game.undo_last_move()
            if child is None:
                return None
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
            child = _solve_value(
                game,
                root_player,
                cache,
                stats,
                depth + 1,
                alpha,
                beta,
                draw_value=draw_value,
                start_time=start_time,
                max_nodes=max_nodes,
                max_seconds=max_seconds,
            )
            game.undo_last_move()
            if child is None:
                return None
            if child < value:
                value = child
            if value < beta:
                beta = value
            if alpha >= beta:
                break

    cache[key] = value
    return value


def solve_root_exact(game, root_player=None, draw_value=0.5, max_nodes=0, max_seconds=0.0):
    player = root_player or game.next_to_move
    legal = game.legal_moves()
    if not legal:
        return None, {}, ExactSearchStats()
    if len(legal) == 1:
        move = legal[0]
        game.make_move(move[0], move[1], game.next_to_move)
        score = _terminal_value(game, player, draw_value=draw_value)
        if score is None:
            score = float(draw_value)
        game.undo_last_move()
        return move, {move: score}, ExactSearchStats(nodes_evaluated=1, max_depth=1)

    cache = {}
    stats = ExactSearchStats()
    start_time = time.time()
    move_values = {}
    best_move = None
    best_value = -1.0

    for move in legal:
        if _limits_hit(stats, start_time, max_nodes, max_seconds):
            stats.truncated = True
            return None, move_values, stats
        game.make_move(move[0], move[1], game.next_to_move)
        value = _solve_value(
            game,
            player,
            cache,
            stats,
            1,
            0.0,
            1.0,
            draw_value=draw_value,
            start_time=start_time,
            max_nodes=max_nodes,
            max_seconds=max_seconds,
        )
        game.undo_last_move()
        if value is None:
            stats.truncated = True
            return None, move_values, stats
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
