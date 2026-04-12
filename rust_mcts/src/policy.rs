use crate::eval::{
    evaluate_game_state_baseline, evaluate_game_state_pragmatic,
    score_local_board, PolicyConfig, CELL_BONUS,
};
use crate::game::{Game, Move, Player, Winner};

// ---------------------------------------------------------------------------
// Policy types
// ---------------------------------------------------------------------------

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PolicyType {
    Baseline,
    Pragmatic,
    GraphPuct,
}

impl PolicyType {
    pub fn from_str(s: &str) -> PolicyType {
        match s {
            "pragmatic" => PolicyType::Pragmatic,
            "graph_puct" => PolicyType::GraphPuct,
            _ => PolicyType::Baseline,
        }
    }
}

// ---------------------------------------------------------------------------
// Shared evaluation dispatcher
// ---------------------------------------------------------------------------

pub fn evaluate(game: &Game, player: Player, policy: PolicyType, cfg: &PolicyConfig) -> f64 {
    match policy {
        PolicyType::Baseline => evaluate_game_state_baseline(&game.board, player, cfg),
        PolicyType::Pragmatic | PolicyType::GraphPuct => {
            evaluate_game_state_pragmatic(&game.board, player, cfg)
        }
    }
}

// ---------------------------------------------------------------------------
// Opponent immediate global win check (shared by Pragmatic + GraphPuct)
// ---------------------------------------------------------------------------

fn opponent_immediate_global_win_exists(game: &mut Game, opponent: Player) -> bool {
    let legal = game.legal_moves();
    for mv in legal {
        game.make_move(mv.0, mv.1);
        // After the opponent's move we need to check if THEY won.
        // But wait — opponent isn't necessarily game.next_to_move here.
        // In Python: game.make_move(move[0], move[1], opponent) checks that
        // `opponent == game.next_to_move`, so it only succeeds if it's their turn.
        // Here we just made the move unconditionally; we're already in the position
        // where opponent is to_move (since we just un-did a player move above this call).
        let won = game.board.winner == opponent.to_winner();
        game.undo_last_move();
        if won {
            return true;
        }
    }
    false
}

// ---------------------------------------------------------------------------
// Rollout policies
// ---------------------------------------------------------------------------

/// Baseline: purely random rollout.
pub fn rollout_move_baseline(game: &Game) -> Option<Move> {
    let legal = game.legal_moves();
    if legal.is_empty() {
        return Option::None;
    }
    // Return first legal move (fast; randomness matters less when there are
    // many rollouts and positions cycle through them naturally).
    Some(legal[0])
}

/// Pragmatic: pick the highest-scoring move by quick heuristic evaluation.
/// Mirrors PragmaticMCTSPolicy._quick_move_value.
pub fn rollout_move_pragmatic(game: &mut Game, cfg: &PolicyConfig) -> Option<Move> {
    let legal = game.legal_moves();
    if legal.is_empty() {
        return Option::None;
    }
    let player = game.next_to_move;
    let opponent = player.opponent();

    let mut best_move = legal[0];
    let mut best_score = f64::NEG_INFINITY;

    for mv in &legal {
        let score = quick_move_value(game, *mv, player, opponent, cfg);
        if score > best_score {
            best_score = score;
            best_move = *mv;
        }
    }
    Some(best_move)
}

fn quick_move_value(
    game: &mut Game,
    mv: Move,
    player: Player,
    opponent: Player,
    cfg: &PolicyConfig,
) -> f64 {
    game.make_move(mv.0, mv.1);

    let mut score = 0.0f64;
    if game.board.winner == player.to_winner() {
        score += 10.0;
    }
    if game.board.mini_boards[mv.0 as usize].winner == player.to_winner() {
        score += 1.4;
    }
    score += CELL_BONUS[mv.1 as usize];
    score += 0.30 * evaluate_game_state_pragmatic(&game.board, player, cfg);
    if opponent_immediate_global_win_exists(game, opponent) {
        score -= 6.0;
    }

    game.undo_last_move();
    score
}

/// GraphPuct rollout: same heuristic as pragmatic.
pub fn rollout_move_graph_puct(game: &mut Game, cfg: &PolicyConfig) -> Option<Move> {
    rollout_move_pragmatic(game, cfg)
}

// ---------------------------------------------------------------------------
// GraphPuct prior probabilities
// Mirrors GraphPUCTPolicy.priors
// ---------------------------------------------------------------------------

pub fn compute_priors(
    game: &mut Game,
    legal: &[Move],
    cfg: &PolicyConfig,
) -> Vec<(Move, f64)> {
    let player = game.next_to_move;
    let opponent = player.opponent();

    let mut raw: Vec<(Move, f64)> = Vec::with_capacity(legal.len());
    let mut min_score = f64::INFINITY;

    for &mv in legal {
        let s = move_tactical_score(game, mv, player, opponent, cfg);
        if s < min_score {
            min_score = s;
        }
        raw.push((mv, s));
    }

    // Shift to positive and normalise
    let shifted: Vec<(Move, f64)> = raw
        .iter()
        .map(|&(mv, v)| (mv, v - min_score + 1e-3))
        .collect();
    let denom: f64 = shifted.iter().map(|(_, v)| v).sum::<f64>().max(1e-9);
    shifted
        .into_iter()
        .map(|(mv, v)| (mv, v / denom))
        .collect()
}

fn forced_board_control_score(
    game: &Game,
    mv: Move,
    player: Player,
    cfg: &PolicyConfig,
) -> f64 {
    let target_idx = mv.1 as usize;
    let target_board = &game.board.mini_boards[target_idx];
    let target_open =
        target_board.winner == Winner::None && target_board.cells.iter().any(|&c| c == crate::game::Cell::Empty);
    if !target_open {
        return -0.30;
    }
    let board_weight = if target_idx == 4 {
        1.0
    } else if matches!(target_idx, 0 | 2 | 6 | 8) {
        0.9
    } else {
        0.8
    };
    let lp = score_local_board(&target_board.cells, player, cfg);
    let lo = score_local_board(&target_board.cells, player.opponent(), cfg);
    0.35 * board_weight * (lp - lo)
}

fn move_tactical_score(
    game: &mut Game,
    mv: Move,
    player: Player,
    opponent: Player,
    cfg: &PolicyConfig,
) -> f64 {
    game.make_move(mv.0, mv.1);

    let mut score = 0.0f64;
    if game.board.winner == player.to_winner() {
        score += 10.0;
    }
    if game.board.mini_boards[mv.0 as usize].winner == player.to_winner() {
        score += 1.2;
    }
    score += CELL_BONUS[mv.1 as usize];
    score += forced_board_control_score(game, mv, player, cfg);
    score += 0.25 * evaluate_game_state_pragmatic(&game.board, player, cfg);
    if opponent_immediate_global_win_exists(game, opponent) {
        score -= 4.0;
    }

    game.undo_last_move();
    score
}

// ---------------------------------------------------------------------------
// select_final_move
// ---------------------------------------------------------------------------

/// Baseline: highest visit count.
pub fn select_final_move_baseline(
    best_move: Move,
    _game: &Game,
    _cfg: &PolicyConfig,
) -> Move {
    best_move
}

/// Pragmatic: priority ordering identical to Python PragmaticMCTSPolicy.select_final_move.
/// `move_stats` = (move, mean_score, rollouts) for each legal move.
pub fn select_final_move_pragmatic(
    game: &mut Game,
    move_stats: &[(Move, f64, u32)],
    cfg: &PolicyConfig,
) -> Option<Move> {
    let player = game.next_to_move;
    let opponent = player.opponent();
    let legal: Vec<Move> = move_stats.iter().map(|(m, _, _)| *m).collect();
    if legal.is_empty() {
        return Option::None;
    }

    // Check if opponent has a direct global win RIGHT NOW (before any move).
    let opp_direct_win_now = {
        // Temporarily let opponent move
        let orig_next = game.next_to_move;
        game.next_to_move = opponent;
        let result = opponent_immediate_global_win_exists(game, opponent);
        game.next_to_move = orig_next;
        result
    };

    let mut best_move: Option<Move> = Option::None;
    let mut best_key: Option<(i32, i32, i32, i32, i64, i64, i32, i32)> = Option::None;

    for &(mv, mean_score, rollouts) in move_stats {
        game.make_move(mv.0, mv.1);

        let immediate_global_win = (game.board.winner == player.to_winner()) as i32;
        let immediate_local_win =
            (game.board.mini_boards[mv.0 as usize].winner == player.to_winner()) as i32;

        let blocks_opp_global = if opp_direct_win_now {
            // After our move, does opponent still have an immediate win?
            let still_has_win = opponent_immediate_global_win_exists(game, opponent);
            (!still_has_win) as i32
        } else {
            0i32
        };

        game.undo_last_move();

        // Compute threat level of this move
        let threat_level = opponent_threat_level_after_move(game, mv, player, cfg);

        // Build comparison key (higher = better).
        // Python uses: (immediate_global_win, blocks_opp_global, immediate_local_win,
        //               -threat_level, mean_score, rollouts, -move[0], -move[1])
        // We encode mean_score and rollouts as integers scaled up to keep ordering.
        let key = (
            immediate_global_win,
            blocks_opp_global,
            immediate_local_win,
            -threat_level,
            (mean_score * 1e9) as i64,
            rollouts as i64,
            -(mv.0 as i32),
            -(mv.1 as i32),
        );

        if best_key.is_none() || key > best_key.unwrap() {
            best_key = Some(key);
            best_move = Some(mv);
        }
    }
    best_move
}

fn opponent_threat_level_after_move(
    game: &mut Game,
    mv: Move,
    player: Player,
    _cfg: &PolicyConfig,
) -> i32 {
    let opponent = player.opponent();
    game.make_move(mv.0, mv.1);

    let mut threat_level = 0i32;
    for opp_mv in game.legal_moves() {
        game.make_move(opp_mv.0, opp_mv.1);
        if game.board.winner == opponent.to_winner() {
            threat_level = 2;
            game.undo_last_move();
            break;
        }
        if game.board.mini_boards[opp_mv.0 as usize].winner == opponent.to_winner() {
            threat_level = threat_level.max(1);
        }
        game.undo_last_move();
    }

    game.undo_last_move();
    threat_level
}

/// GraphPuct final move: most-visited, tie-break by Q then move index.
pub fn select_final_move_graph_puct(
    game: &Game,
    edge_visits: &rustc_hash::FxHashMap<Move, u32>,
    edge_q: impl Fn(Move) -> f64,
) -> Option<Move> {
    let legal = game.legal_moves();
    if legal.is_empty() {
        return Option::None;
    }
    let mut best: Option<Move> = Option::None;
    let mut best_key: Option<(u32, i64, i32, i32)> = Option::None;

    for mv in legal {
        let visits = edge_visits.get(&mv).copied().unwrap_or(0);
        let q = edge_q(mv);
        let key = (visits, (q * 1e9) as i64, -(mv.0 as i32), -(mv.1 as i32));
        if best_key.is_none() || key > best_key.unwrap() {
            best_key = Some(key);
            best = Some(mv);
        }
    }
    best
}
