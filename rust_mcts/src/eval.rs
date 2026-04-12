use crate::game::{Cell, MiniBoard, Board, Player, Winner, WIN_LINES};

// Position bonus for CELL_BONUS[cell_idx]: corners > edges, center best
pub const CELL_BONUS: [f64; 9] = [0.18, 0.04, 0.18, 0.04, 0.24, 0.04, 0.18, 0.04, 0.18];

/// All the config knobs that come in from Python.
/// Filled with defaults; overridden from the config dict.
#[derive(Clone, Debug)]
pub struct PolicyConfig {
    // score_local_board params
    pub base_potential: f64,
    pub line_exponent: f64,
    pub max_multiplier: f64,
    pub weight_best: f64,
    pub weight_path: f64,
    pub max_score: f64,
    // calculate_square_importance params
    pub importance_win_weight: f64,
    pub importance_develop_weight: f64,
    pub importance_fresh_weight: f64,
    // evaluate_game_state params
    pub global_score_weight: f64,
    pub strategic_score_weight: f64,
    pub offensive_weight: f64,
    pub defensive_weight: f64,
    pub final_max_score: f64,
    pub terminal_draw_value: f64,
    // Pragmatic / graph-puct extras
    pub won_board_bonus: f64,
    pub open_two_bonus: f64,
    // Search params
    pub ucb_constant: f64,
    pub rollout_depth: usize,
    pub c_puct: f64,
    // Exact-endgame thresholds (-1 = disabled)
    pub exact_endgame_legal_cells_threshold: i32,
    pub exact_endgame_empty_cells_threshold: i32,
}

impl PolicyConfig {
    pub fn from_map(m: &std::collections::HashMap<String, f64>) -> Self {
        let g = |k: &str, d: f64| -> f64 { m.get(k).copied().unwrap_or(d) };
        PolicyConfig {
            base_potential: g("base_potential", 0.15),
            line_exponent: g("line_exponent", 1.5),
            max_multiplier: g("max_multiplier", 1.5),
            weight_best: g("weight_best", 0.6),
            weight_path: g("weight_path", 0.4),
            max_score: g("max_score", 0.9),
            importance_win_weight: g("importance_win_weight", 2.0),
            importance_develop_weight: g("importance_develop_weight", 0.3),
            importance_fresh_weight: g("importance_fresh_weight", 0.1),
            global_score_weight: g("global_score_weight", 0.65),
            strategic_score_weight: g("strategic_score_weight", 0.35),
            offensive_weight: g("offensive_weight", 0.7),
            defensive_weight: g("defensive_weight", 0.3),
            final_max_score: g("final_max_score", 0.9),
            terminal_draw_value: g("terminal_draw_value", 0.5),
            won_board_bonus: g("won_board_bonus", 0.0),
            open_two_bonus: g("open_two_bonus", 0.0),
            ucb_constant: g("ucb_constant", 1.414),
            rollout_depth: g("rollout_depth", 6.0) as usize,
            c_puct: g("c_puct", 1.4),
            exact_endgame_legal_cells_threshold: g("exact_endgame_legal_cells_threshold", -1.0) as i32,
            exact_endgame_empty_cells_threshold: {
                // Support legacy key name too
                let v = g("exact_endgame_empty_cells_threshold",
                          g("exact_endgame_threshold", -1.0));
                v as i32
            },
        }
    }
}

// ---------------------------------------------------------------------------
// score_local_board  (port of bots/baseline_mcts/eval.py:score_local_board)
// ---------------------------------------------------------------------------

/// Score a 9-cell board (mini board or global board) for `player`.
/// `cells` may represent actual mini-board cells or a global board view
/// where each slot is the winner of a mini board (Cell::Empty for unowned).
pub fn score_local_board(cells: &[Cell; 9], player: Player, cfg: &PolicyConfig) -> f64 {
    let player_cell = player.to_cell();
    let opp_cell = player.opponent().to_cell();
    let mut potentials: Vec<f64> = Vec::with_capacity(8);

    for &[a, b, c] in &WIN_LINES {
        let ca = cells[a];
        let cb = cells[b];
        let cc = cells[c];

        let pc = [ca, cb, cc].iter().filter(|&&x| x == player_cell).count();
        let oc = [ca, cb, cc].iter().filter(|&&x| x == opp_cell).count();

        if pc == 3 {
            return 1.0;
        }
        if oc == 3 {
            return 0.0;
        }
        if pc > 0 && oc > 0 {
            continue; // blocked line
        }
        if oc == 0 {
            let potential =
                cfg.base_potential + (pc as f64 / 3.0).powf(cfg.line_exponent);
            potentials.push(potential);
        }
    }

    if potentials.is_empty() {
        return 0.0;
    }

    let best_line = potentials.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    let num_paths = potentials.len();
    potentials.sort_by(|a, b| b.partial_cmp(a).unwrap());
    let path_synergy: f64 = potentials.iter().take(4).sum::<f64>() / 4.0;
    let path_multiplier = cfg.max_multiplier.min(1.0 + num_paths as f64 / 8.0);
    let path_strength = path_synergy * path_multiplier;

    let score = cfg.weight_best * best_line + cfg.weight_path * path_strength;
    score.min(cfg.max_score)
}

// ---------------------------------------------------------------------------
// calculate_square_importance  (port of bots/baseline_mcts/eval.py)
// ---------------------------------------------------------------------------

fn count_viable_paths(cells: &[Cell; 9], player: Player) -> usize {
    let opp = player.opponent().to_cell();
    WIN_LINES
        .iter()
        .filter(|&&[a, b, c]| cells[a] != opp && cells[b] != opp && cells[c] != opp)
        .count()
}

/// Returns (importance_player, importance_opponent) arrays of length 9.
pub fn calculate_square_importance(
    cells: &[Cell; 9],
    player: Player,
    cfg: &PolicyConfig,
) -> ([f64; 9], [f64; 9]) {
    let opponent = player.opponent();
    let player_cell = player.to_cell();
    let opp_cell = opponent.to_cell();

    let viable_x = count_viable_paths(cells, player);
    let viable_o = count_viable_paths(cells, opponent);

    let mut imp_p = [0.0f64; 9];
    let mut imp_o = [0.0f64; 9];

    for &[a, b, c] in &WIN_LINES {
        let line = [cells[a], cells[b], cells[c]];
        let p_count = line.iter().filter(|&&x| x == player_cell).count();
        let o_count = line.iter().filter(|&&x| x == opp_cell).count();

        // If either player has a full line, both arrays go to zero
        if p_count == 3 || o_count == 3 {
            return ([0.0; 9], [0.0; 9]);
        }

        let empty_indices: Vec<usize> = [a, b, c]
            .iter()
            .filter(|&&i| cells[i] == Cell::Empty)
            .copied()
            .collect();
        if empty_indices.is_empty() {
            continue;
        }

        let imp_p_line = if viable_x == 0 || o_count > 0 {
            0.0
        } else if p_count == 2 {
            (cfg.importance_win_weight / viable_x as f64).min(1.0)
        } else if p_count == 1 {
            cfg.importance_develop_weight / viable_x as f64
        } else {
            cfg.importance_fresh_weight / viable_x as f64
        };

        let imp_o_line = if viable_o == 0 || p_count > 0 {
            0.0
        } else if o_count == 2 {
            (cfg.importance_win_weight / viable_o as f64).min(1.0)
        } else if o_count == 1 {
            cfg.importance_develop_weight / viable_o as f64
        } else {
            cfg.importance_fresh_weight / viable_o as f64
        };

        for &idx in &empty_indices {
            imp_p[idx] += imp_p_line;
            imp_o[idx] += imp_o_line;
        }
    }

    // Normalize
    let max_p = imp_p.iter().cloned().fold(0.0f64, f64::max).max(1.0);
    let max_o = imp_o.iter().cloned().fold(0.0f64, f64::max).max(1.0);
    for v in &mut imp_p {
        *v = (1.0f64).min(*v / max_p);
    }
    for v in &mut imp_o {
        *v = (1.0f64).min(*v / max_o);
    }

    (imp_p, imp_o)
}

// ---------------------------------------------------------------------------
// Helpers to build a Cell-view of the global board
// ---------------------------------------------------------------------------

pub fn mini_winners_as_cells(mini_boards: &[MiniBoard; 9]) -> [Cell; 9] {
    std::array::from_fn(|i| match mini_boards[i].winner {
        Winner::X => Cell::X,
        Winner::O => Cell::O,
        _ => Cell::Empty, // None or (shouldn't happen) Draw for mini boards
    })
}

// ---------------------------------------------------------------------------
// evaluate_game_state  (port of bots/baseline_mcts/eval.py:evaluate_game_state)
// ---------------------------------------------------------------------------

pub fn evaluate_game_state_baseline(board: &Board, player: Player, cfg: &PolicyConfig) -> f64 {
    let opponent = player.opponent();
    let draw_value = cfg.terminal_draw_value;

    if board.winner == player.to_winner() {
        return 1.0;
    }
    if board.winner == opponent.to_winner() {
        return 0.0;
    }
    if board.winner == Winner::Draw {
        return draw_value;
    }

    let has_playable = board.mini_boards.iter().any(|m| {
        m.winner == Winner::None && m.cells.iter().any(|&c| c == Cell::Empty)
    });
    if !has_playable || !board.has_viable_big_board_line() {
        return draw_value;
    }

    let global_cells = mini_winners_as_cells(&board.mini_boards);
    let (global_imp_p, global_imp_o) =
        calculate_square_importance(&global_cells, player, cfg);
    let global_score = score_local_board(&global_cells, player, cfg);

    let mut strategic_score = 0.0f64;
    let mut total_weight = 0.0f64;

    for (i, mini) in board.mini_boards.iter().enumerate() {
        if mini.winner != Winner::None {
            continue;
        }
        let wp = score_local_board(&mini.cells, player, cfg);
        let wo = score_local_board(&mini.cells, opponent, cfg);
        let board_importance = global_imp_p[i].max(global_imp_o[i]);
        let board_score = cfg.offensive_weight * wp * global_imp_p[i]
            - cfg.defensive_weight * wo * global_imp_o[i];
        strategic_score += board_score * board_importance;
        total_weight += board_importance;
    }

    if total_weight > 0.0 {
        strategic_score = (strategic_score / total_weight + 1.0) / 2.0;
    } else {
        strategic_score = 0.0;
    }

    let final_score =
        cfg.global_score_weight * global_score + cfg.strategic_score_weight * strategic_score;
    (0.0f64).max(final_score.min(cfg.final_max_score))
}

// ---------------------------------------------------------------------------
// count_open_twos  (port of bots/pragmatic_mcts/eval.py)
// ---------------------------------------------------------------------------

pub fn count_open_twos(cells: &[Cell; 9], player: Player) -> usize {
    let player_cell = player.to_cell();
    let opp_cell = player.opponent().to_cell();
    WIN_LINES
        .iter()
        .filter(|&&[a, b, c]| {
            let line = [cells[a], cells[b], cells[c]];
            let pc = line.iter().filter(|&&x| x == player_cell).count();
            let oc = line.iter().filter(|&&x| x == opp_cell).count();
            let ec = line.iter().filter(|&&x| x == Cell::Empty).count();
            pc == 2 && oc == 0 && ec == 1
        })
        .count()
}

// ---------------------------------------------------------------------------
// evaluate_game_state_pragmatic
// (port of bots/pragmatic_mcts/eval.py:evaluate_game_state)
// ---------------------------------------------------------------------------

pub fn evaluate_game_state_pragmatic(board: &Board, player: Player, cfg: &PolicyConfig) -> f64 {
    let base = evaluate_game_state_baseline(board, player, cfg);
    let opponent = player.opponent();

    // Terminal — no bonuses
    if board.winner == player.to_winner()
        || board.winner == opponent.to_winner()
        || board.winner == Winner::Draw
    {
        return base;
    }

    let player_won = board
        .mini_boards
        .iter()
        .filter(|m| m.winner == player.to_winner())
        .count();
    let opp_won = board
        .mini_boards
        .iter()
        .filter(|m| m.winner == opponent.to_winner())
        .count();

    let won_delta = (player_won as f64 - opp_won as f64) / 9.0;
    let won_bonus = cfg.won_board_bonus * won_delta;

    let mut open_two_delta = 0.0f64;
    for mini in &board.mini_boards {
        if mini.winner != Winner::None {
            continue;
        }
        open_two_delta += count_open_twos(&mini.cells, player) as f64;
        open_two_delta -= count_open_twos(&mini.cells, opponent) as f64;
    }
    let open_two_bonus = cfg.open_two_bonus * (open_two_delta / 18.0);

    (0.0f64).max((base + won_bonus + open_two_bonus).min(1.0))
}
