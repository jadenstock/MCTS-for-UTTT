use std::time::Instant;
use rustc_hash::FxHashMap;

use crate::eval::PolicyConfig;
use crate::game::{Game, Move, Player, StateKey};
use crate::policy::{
    compute_priors, evaluate, rollout_move_graph_puct, select_final_move_graph_puct, PolicyType,
};

// ---------------------------------------------------------------------------
// Graph node
// ---------------------------------------------------------------------------

pub struct GraphNode {
    pub priors: FxHashMap<Move, f64>,
    pub visits: u32,
    pub value_sum: f64,
    pub edge_visits: FxHashMap<Move, u32>,
    pub edge_value_sum: FxHashMap<Move, f64>,
}

impl GraphNode {
    pub fn new(priors: FxHashMap<Move, f64>, legal: &[Move]) -> Self {
        let mut edge_visits = FxHashMap::default();
        let mut edge_value_sum = FxHashMap::default();
        for &mv in legal {
            edge_visits.insert(mv, 0u32);
            edge_value_sum.insert(mv, 0.0f64);
        }
        GraphNode {
            priors,
            visits: 0,
            value_sum: 0.0,
            edge_visits,
            edge_value_sum,
        }
    }

    /// Q estimate for an edge.
    /// Biased Q-initialization: unvisited moves look slightly worse than the
    /// node's current average rather than a neutral 0.5, preventing forced
    /// breadth-first sweeps in high-fanout "send-to-any-board" states.
    pub fn edge_q(&self, mv: Move) -> f64 {
        let n = self.edge_visits.get(&mv).copied().unwrap_or(0);
        if n == 0 {
            if self.visits > 0 {
                return self.value_sum / (self.visits + 1) as f64;
            }
            return 0.5;
        }
        self.edge_value_sum.get(&mv).copied().unwrap_or(0.0) / n as f64
    }
}

// ---------------------------------------------------------------------------
// PUCT selection
// ---------------------------------------------------------------------------

fn select_puct_move(
    node: &GraphNode,
    game: &Game,
    root_player: Player,
    c_puct: f64,
) -> Option<Move> {
    let legal = game.legal_moves();
    if legal.is_empty() {
        return Option::None;
    }
    let maximize_root = game.next_to_move == root_player;
    let sqrt_n = (node.visits.max(1) as f64).sqrt();

    let mut best: Option<(Move, f64)> = Option::None;
    for mv in legal {
        let q = node.edge_q(mv);
        let q_eff = if maximize_root { q } else { 1.0 - q };
        let p = node.priors.get(&mv).copied().unwrap_or(1e-3);
        let n = node.edge_visits.get(&mv).copied().unwrap_or(0);
        let u = c_puct * p * (sqrt_n / (1 + n) as f64);
        let s = q_eff + u;

        let better = match best {
            Option::None => true,
            Some((bm, bs)) => s > bs || (s == bs && (mv.0, mv.1) < (bm.0, bm.1)),
        };
        if better {
            best = Some((mv, s));
        }
    }
    best.map(|(mv, _)| mv)
}

// ---------------------------------------------------------------------------
// Rollout
// ---------------------------------------------------------------------------

fn rollout(game: &mut Game, cfg: &PolicyConfig, root_player: Player) -> f64 {
    let mut moves_made = 0usize;
    let mut depth = 0usize;
    while depth < cfg.rollout_depth
        && !game.board.winner.is_terminal()
        && !game.legal_moves().is_empty()
    {
        let mv = match rollout_move_graph_puct(game, cfg) {
            Some(m) => m,
            Option::None => break,
        };
        game.make_move(mv.0, mv.1);
        moves_made += 1;
        depth += 1;
    }
    let value = evaluate(game, root_player, PolicyType::GraphPuct, cfg);
    for _ in 0..moves_made {
        game.undo_last_move();
    }
    value
}

// ---------------------------------------------------------------------------
// Single simulation
// ---------------------------------------------------------------------------

/// Insert a new node for `key` if not already present.
/// Avoids returning a reference to sidestep borrow-checker conflicts when
/// `game` is also needed after the call.
fn ensure_node(
    graph: &mut FxHashMap<StateKey, GraphNode>,
    key: StateKey,
    game: &mut Game,
    cfg: &PolicyConfig,
) {
    if !graph.contains_key(&key) {
        let legal = game.legal_moves();
        let priors_vec = if legal.is_empty() {
            vec![]
        } else {
            compute_priors(game, &legal, cfg)
        };
        let priors: FxHashMap<Move, f64> = priors_vec.into_iter().collect();
        let node = GraphNode::new(priors, &legal);
        graph.insert(key, node);
    }
}

fn run_simulation(
    game: &mut Game,
    cfg: &PolicyConfig,
    graph: &mut FxHashMap<StateKey, GraphNode>,
    root_player: Player,
    forced_root_move: Option<Move>,
) -> usize {
    let mut path: Vec<(StateKey, Move)> = Vec::new();
    let mut moves_made = 0usize;
    let mut depth = 0usize;

    let root_key = game.state_key();
    ensure_node(graph, root_key.clone(), game, cfg);

    // If a specific root move is forced (warm-up pass), take it first
    if let Some(fmv) = forced_root_move {
        let legal = game.legal_moves();
        if !legal.contains(&fmv) {
            return 0;
        }
        path.push((root_key.clone(), fmv));
        game.make_move(fmv.0, fmv.1);
        moves_made += 1;
        depth += 1;

        let child_key = game.state_key();
        if !graph.contains_key(&child_key) {
            ensure_node(graph, child_key.clone(), game, cfg);
            let leaf_value = rollout(game, cfg, root_player);
            backprop(graph, &path, leaf_value);
            for _ in 0..moves_made {
                game.undo_last_move();
            }
            return depth;
        }
    }

    // Main selection loop
    let leaf_value = loop {
        let key = game.state_key();
        let legal = game.legal_moves();

        if legal.is_empty() || game.board.winner.is_terminal() {
            break evaluate(game, root_player, PolicyType::GraphPuct, cfg);
        }

        // select_puct_move needs a reference to the node
        let mv = {
            let node = graph.get(&key).unwrap();
            match select_puct_move(node, game, root_player, cfg.c_puct) {
                Some(m) => m,
                Option::None => {
                    break evaluate(game, root_player, PolicyType::GraphPuct, cfg);
                }
            }
        };

        path.push((key.clone(), mv));
        game.make_move(mv.0, mv.1);
        moves_made += 1;
        depth += 1;

        let child_key = game.state_key();
        if !graph.contains_key(&child_key) {
            ensure_node(graph, child_key, game, cfg);
            break rollout(game, cfg, root_player);
        }
    };

    // Backprop
    backprop(graph, &path, leaf_value);

    // If path was empty (terminal at root), still credit a root visit
    if path.is_empty() {
        let root_key = game.state_key();
        if let Some(node) = graph.get_mut(&root_key) {
            node.visits += 1;
            node.value_sum += leaf_value;
        }
    }

    for _ in 0..moves_made {
        game.undo_last_move();
    }
    depth
}

fn backprop(graph: &mut FxHashMap<StateKey, GraphNode>, path: &[(StateKey, Move)], value: f64) {
    for (state_key, mv) in path {
        if let Some(node) = graph.get_mut(state_key) {
            node.visits += 1;
            node.value_sum += value;
            *node.edge_visits.entry(*mv).or_insert(0) += 1;
            *node.edge_value_sum.entry(*mv).or_insert(0.0) += value;
        }
    }
}

// ---------------------------------------------------------------------------
// Public interface
// ---------------------------------------------------------------------------

pub struct GraphPuctResult {
    pub best_move: Move,
    pub num_gamestates: u32,
    pub depth_explored: usize,
    pub move_stats: Vec<(Move, Option<f64>, u32)>,
    pub thinking_time: f64,
    pub early_stop: bool,
    pub search_type: &'static str,
}

pub fn run_graph_puct(
    game: &mut Game,
    cfg: &PolicyConfig,
    max_seconds: f64,
    max_nodes: u32,
    include_metadata: bool,
) -> Option<GraphPuctResult> {
    use crate::exact_endgame::{count_empty_cells, count_legal_cells, solve_root_exact};

    let legal = game.legal_moves();
    if legal.is_empty() {
        return Option::None;
    }

    // --- Exact endgame check ---
    let use_exact = {
        let legal_threshold = cfg.exact_endgame_legal_cells_threshold;
        let empty_threshold = cfg.exact_endgame_empty_cells_threshold;
        if legal.len() <= 1 {
            false
        } else if legal_threshold >= 0 {
            count_legal_cells(game) <= legal_threshold as usize
        } else if empty_threshold >= 0 {
            count_empty_cells(game) <= empty_threshold as usize
        } else {
            false
        }
    };

    if use_exact {
        let start = Instant::now();
        let root_player = game.next_to_move;
        let (best_move, move_values, stats) = solve_root_exact(
            game,
            root_player,
            cfg.terminal_draw_value,
            max_nodes as u64,
            max_seconds,
        );
        if let Some(bm) = best_move {
            if !stats.truncated {
                let thinking_time = start.elapsed().as_secs_f64();
                let move_stats: Vec<(Move, Option<f64>, u32)> = legal
                    .iter()
                    .map(|&mv| (mv, move_values.get(&mv).copied(), 0))
                    .collect();
                return Some(GraphPuctResult {
                    best_move: bm,
                    num_gamestates: stats.nodes_evaluated as u32,
                    depth_explored: stats.max_depth as usize,
                    move_stats,
                    thinking_time,
                    early_stop: false,
                    search_type: "exact_endgame",
                });
            }
        }
    }

    // --- Single-move shortcut ---
    if legal.len() == 1 {
        let mv = legal[0];
        let player = game.next_to_move;
        game.make_move(mv.0, mv.1);
        let s = evaluate(game, player, PolicyType::GraphPuct, cfg);
        game.undo_last_move();
        return Some(GraphPuctResult {
            best_move: mv,
            num_gamestates: 0,
            depth_explored: 0,
            move_stats: vec![(mv, Some(s), 0)],
            thinking_time: 0.0,
            early_stop: true,
            search_type: "graph_puct",
        });
    }

    // --- Main Graph PUCT loop ---
    let root_player = game.next_to_move;
    let mut graph: FxHashMap<StateKey, GraphNode> = FxHashMap::default();
    let root_key = game.state_key();
    ensure_node(&mut graph, root_key.clone(), game, cfg);

    let start = Instant::now();
    let mut iterations = 0u32;
    let mut max_depth = 0usize;

    // Warm-up: ensure every root move is sampled at least once
    let root_moves = legal.clone();
    for &rmv in &root_moves {
        if start.elapsed().as_secs_f64() > max_seconds || iterations >= max_nodes {
            break;
        }
        let root_node = graph.get(&root_key).unwrap();
        if root_node.edge_visits.get(&rmv).copied().unwrap_or(0) > 0 {
            continue;
        }
        let d = run_simulation(game, cfg, &mut graph, root_player, Some(rmv));
        max_depth = max_depth.max(d);
        iterations += 1;
    }

    // Main loop
    while start.elapsed().as_secs_f64() <= max_seconds && iterations < max_nodes {
        let d = run_simulation(game, cfg, &mut graph, root_player, Option::None);
        max_depth = max_depth.max(d);
        iterations += 1;
    }

    let root_node = graph.get(&root_key)?;

    let best_move = {
        let ev = &root_node.edge_visits;
        let eq = |mv: Move| root_node.edge_q(mv);
        select_final_move_graph_puct(game, ev, eq)?
    };

    let thinking_time = start.elapsed().as_secs_f64();

    let move_stats: Vec<(Move, Option<f64>, u32)> = legal
        .iter()
        .map(|&mv| {
            let visits = root_node.edge_visits.get(&mv).copied().unwrap_or(0);
            let q = if visits > 0 {
                Some(root_node.edge_q(mv))
            } else {
                Option::None
            };
            (mv, q, visits)
        })
        .collect();

    Some(GraphPuctResult {
        best_move,
        num_gamestates: iterations,
        depth_explored: max_depth,
        move_stats,
        thinking_time,
        early_stop: false,
        search_type: "graph_puct",
    })
}
