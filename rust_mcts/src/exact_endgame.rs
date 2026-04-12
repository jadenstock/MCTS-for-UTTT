use std::time::Instant;
use rustc_hash::FxHashMap;

use crate::game::{Game, Move, Player, StateKey, Winner};

pub struct ExactSearchStats {
    pub nodes_evaluated: u64,
    pub cache_hits: u64,
    pub max_depth: u32,
    pub truncated: bool,
}

impl ExactSearchStats {
    pub fn new() -> Self {
        ExactSearchStats {
            nodes_evaluated: 0,
            cache_hits: 0,
            max_depth: 0,
            truncated: false,
        }
    }
}

pub fn count_empty_cells(game: &Game) -> usize {
    game.board
        .mini_boards
        .iter()
        .flat_map(|m| m.cells.iter())
        .filter(|&&c| c == crate::game::Cell::Empty)
        .count()
}

pub fn count_legal_cells(game: &Game) -> usize {
    game.board
        .mini_boards
        .iter()
        .filter(|m| m.winner == Winner::None)
        .flat_map(|m| m.cells.iter())
        .filter(|&&c| c == crate::game::Cell::Empty)
        .count()
}

fn terminal_value(game: &Game, root_player: Player, draw_value: f64) -> Option<f64> {
    let opp = root_player.opponent();
    if game.board.winner == root_player.to_winner() {
        return Some(1.0);
    }
    if game.board.winner == opp.to_winner() {
        return Some(0.0);
    }
    if game.board.winner == Winner::Draw {
        return Some(draw_value);
    }
    let legal = game.legal_moves();
    if legal.is_empty() {
        return Some(draw_value);
    }
    Option::None
}

fn limits_hit(
    stats: &ExactSearchStats,
    start: &Instant,
    max_nodes: u64,
    max_seconds: f64,
) -> bool {
    if max_nodes > 0 && stats.nodes_evaluated >= max_nodes {
        return true;
    }
    if max_seconds > 0.0 && start.elapsed().as_secs_f64() >= max_seconds {
        return true;
    }
    false
}

fn solve_value(
    game: &mut Game,
    root_player: Player,
    cache: &mut FxHashMap<StateKey, f64>,
    stats: &mut ExactSearchStats,
    depth: u32,
    mut alpha: f64,
    mut beta: f64,
    draw_value: f64,
    start: &Instant,
    max_nodes: u64,
    max_seconds: f64,
) -> Option<f64> {
    if limits_hit(stats, start, max_nodes, max_seconds) {
        stats.truncated = true;
        return Option::None;
    }
    stats.nodes_evaluated += 1;
    if depth > stats.max_depth {
        stats.max_depth = depth;
    }

    if let Some(v) = terminal_value(game, root_player, draw_value) {
        return Some(v);
    }

    let key = game.state_key();
    if let Some(&cached) = cache.get(&key) {
        stats.cache_hits += 1;
        return Some(cached);
    }

    let legal = game.legal_moves();
    let maximizing = game.next_to_move == root_player;

    let value = if maximizing {
        let mut best = -1.0f64;
        for mv in legal {
            game.make_move(mv.0, mv.1);
            let child = solve_value(
                game, root_player, cache, stats,
                depth + 1, alpha, beta, draw_value, start, max_nodes, max_seconds,
            );
            game.undo_last_move();
            let child = child?;
            if child > best {
                best = child;
            }
            if best > alpha {
                alpha = best;
            }
            if alpha >= beta {
                break;
            }
        }
        best
    } else {
        let mut best = 2.0f64;
        for mv in legal {
            game.make_move(mv.0, mv.1);
            let child = solve_value(
                game, root_player, cache, stats,
                depth + 1, alpha, beta, draw_value, start, max_nodes, max_seconds,
            );
            game.undo_last_move();
            let child = child?;
            if child < best {
                best = child;
            }
            if best < beta {
                beta = best;
            }
            if alpha >= beta {
                break;
            }
        }
        best
    };

    cache.insert(key, value);
    Some(value)
}

/// Solve from the root, returning best move, per-move values, and stats.
pub fn solve_root_exact(
    game: &mut Game,
    root_player: Player,
    draw_value: f64,
    max_nodes: u64,
    max_seconds: f64,
) -> (Option<Move>, FxHashMap<Move, f64>, ExactSearchStats) {
    let legal = game.legal_moves();
    if legal.is_empty() {
        return (Option::None, FxHashMap::default(), ExactSearchStats::new());
    }
    if legal.len() == 1 {
        let mv = legal[0];
        game.make_move(mv.0, mv.1);
        let score = terminal_value(game, root_player, draw_value)
            .unwrap_or(draw_value);
        game.undo_last_move();
        let mut move_values = FxHashMap::default();
        move_values.insert(mv, score);
        let mut stats = ExactSearchStats::new();
        stats.nodes_evaluated = 1;
        stats.max_depth = 1;
        return (Some(mv), move_values, stats);
    }

    let mut cache: FxHashMap<StateKey, f64> = FxHashMap::default();
    let mut stats = ExactSearchStats::new();
    let start = Instant::now();
    let mut move_values: FxHashMap<Move, f64> = FxHashMap::default();
    let mut best_move: Option<Move> = Option::None;
    let mut best_value = -1.0f64;

    for mv in legal {
        if limits_hit(&stats, &start, max_nodes, max_seconds) {
            stats.truncated = true;
            return (Option::None, move_values, stats);
        }
        game.make_move(mv.0, mv.1);
        let value = solve_value(
            game, root_player, &mut cache, &mut stats,
            1, 0.0, 1.0, draw_value, &start, max_nodes, max_seconds,
        );
        game.undo_last_move();

        let value = match value {
            Some(v) => v,
            Option::None => {
                stats.truncated = true;
                return (Option::None, move_values, stats);
            }
        };
        move_values.insert(mv, value);

        let is_better = match best_move {
            Option::None => true,
            Some(bm) => {
                let bv = best_value;
                // Tie-break: prefer lower board_idx, then lower cell_idx
                value > bv || (value == bv && (mv.0, mv.1) < (bm.0, bm.1))
            }
        };
        if is_better {
            best_move = Some(mv);
            best_value = value;
        }
    }

    (best_move, move_values, stats)
}
