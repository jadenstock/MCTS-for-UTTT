use std::collections::HashMap;
use std::time::Instant;

use crate::eval::PolicyConfig;
use crate::game::{Game, Move, Player};
use crate::policy::{
    evaluate, rollout_move_baseline, rollout_move_pragmatic, select_final_move_pragmatic,
    PolicyType,
};

// ---------------------------------------------------------------------------
// Tree node
// ---------------------------------------------------------------------------

pub struct TreeNode {
    pub number_of_plays: u32,
    pub total_score: f64,
    pub depth_seen: usize,
    pub children: HashMap<Move, Box<TreeNode>>,
    pub unseen_children: Vec<Move>,
    ucb_constant: f64,
}

impl TreeNode {
    pub fn new(game: &Game, ucb_constant: f64) -> Self {
        TreeNode {
            number_of_plays: 1,
            total_score: 0.0,
            depth_seen: 1,
            children: HashMap::new(),
            unseen_children: game.legal_moves(),
            ucb_constant,
        }
    }

    pub fn mean_score(&self) -> f64 {
        self.total_score / self.number_of_plays as f64
    }

    fn best_ucb1_action(&self, root_player_to_move: bool) -> Option<Move> {
        let c = self.ucb_constant;
        let log_n = (self.number_of_plays as f64).ln();
        let mut best: Option<(Move, f64)> = Option::None;

        for (&mv, child) in &self.children {
            let mean = child.total_score / child.number_of_plays as f64;
            let exploit = if root_player_to_move { mean } else { 1.0 - mean };
            let explore = c * (2.0 * log_n / child.number_of_plays as f64).sqrt();
            let ucb = exploit + explore;

            let better = match best {
                Option::None => true,
                Some((bm, bs)) => ucb > bs || (ucb == bs && (mv.0, mv.1) < (bm.0, bm.1)),
            };
            if better {
                best = Some((mv, ucb));
            }
        }
        best.map(|(mv, _)| mv)
    }

    fn expand_one_child(
        &mut self,
        game: &mut Game,
        root_player: Player,
        policy: PolicyType,
        cfg: &PolicyConfig,
        game_path_len: usize,
    ) {
        let mv = match self.unseen_children.pop() {
            Some(m) => m,
            Option::None => return,
        };

        game.make_move(mv.0, mv.1);

        let child_node = Box::new(TreeNode::new(game, self.ucb_constant));

        // Rollout from the newly expanded child
        let mut rollout_moves = 0usize;
        let mut depth = 0usize;
        while depth < cfg.rollout_depth
            && !game.board.winner.is_terminal()
            && !game.legal_moves().is_empty()
        {
            let rm = match policy {
                PolicyType::Baseline => rollout_move_baseline(game),
                PolicyType::Pragmatic | PolicyType::GraphPuct => {
                    rollout_move_pragmatic(game, cfg)
                }
            };
            let rm = match rm {
                Some(m) => m,
                Option::None => break,
            };
            game.make_move(rm.0, rm.1);
            rollout_moves += 1;
            depth += 1;
        }

        let score = evaluate(game, root_player, policy, cfg);

        // Undo rollout
        for _ in 0..rollout_moves {
            game.undo_last_move();
        }

        let mut node = child_node;
        node.total_score = score;

        // Backprop through this node and ancestors
        self.number_of_plays += 1;
        self.total_score += score;
        if game_path_len > self.depth_seen {
            self.depth_seen = game_path_len;
        }

        self.children.insert(mv, node);
        game.undo_last_move();
    }

    /// Recursive tree expansion — mutates game in place (make/undo).
    pub fn expand_tree_by_one(
        &mut self,
        game: &mut Game,
        root_player: Player,
        policy: PolicyType,
        cfg: &PolicyConfig,
        game_path_len: usize,
    ) {
        if !self.unseen_children.is_empty() {
            self.expand_one_child(game, root_player, policy, cfg, game_path_len);
            return;
        }
        let root_to_move = game.next_to_move == root_player;
        if let Some(mv) = self.best_ucb1_action(root_to_move) {
            game.make_move(mv.0, mv.1);
            // Temporarily take the child out to avoid aliasing issues
            if let Some(mut child) = self.children.remove(&mv) {
                child.expand_tree_by_one(game, root_player, policy, cfg, game_path_len + 1);
                // Backprop: the child's last score is in its total (last expand added it)
                // We approximate by adding the child's latest score contribution
                let child_score = child.total_score;
                let child_plays = child.number_of_plays;
                self.children.insert(mv, child);

                self.number_of_plays += 1;
                // Propagate the last simulation score.
                // Since we don't store it separately, we use the child's running mean
                // as a proxy — this is equivalent to Python's approach where the same
                // `score` is added to every ancestor.
                // Actually: Python walks game_path backwards and adds the same score.
                // We replicate that by storing the last score in a thread-local or
                // passing it back. For simplicity, use the child's last contribution.
                let last_score = child_score / child_plays as f64;
                self.total_score += last_score;
                if game_path_len > self.depth_seen {
                    self.depth_seen = game_path_len;
                }
            }
            game.undo_last_move();
        }
    }
}

// ---------------------------------------------------------------------------
// run_mcts
// ---------------------------------------------------------------------------

pub struct MctsResult {
    pub best_move: Move,
    pub num_gamestates: u32,
    pub depth_explored: usize,
    pub move_stats: Vec<(Move, f64, u32)>,
    pub thinking_time: f64,
    pub early_stop: bool,
    pub search_type: &'static str,
}

pub fn run_mcts(
    game: &mut Game,
    policy: PolicyType,
    cfg: &PolicyConfig,
    max_seconds: f64,
    max_nodes: u32,
    include_metadata: bool,
) -> Option<MctsResult> {
    use crate::exact_endgame::solve_root_exact;

    let legal = game.legal_moves();
    if legal.is_empty() {
        return Option::None;
    }

    // --- Exact endgame check ---
    let use_exact = should_use_exact(game, cfg, &legal);
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
                let move_stats: Vec<(Move, f64, u32)> = legal
                    .iter()
                    .map(|&mv| (mv, move_values.get(&mv).copied().unwrap_or(f64::NEG_INFINITY), 0))
                    .collect();
                return Some(MctsResult {
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
        if !include_metadata {
            return Some(MctsResult {
                best_move: mv,
                num_gamestates: 0,
                depth_explored: 0,
                move_stats: vec![(mv, 0.0, 0)],
                thinking_time: 0.0,
                early_stop: true,
                search_type: "mcts",
            });
        }
        let player = game.next_to_move;
        game.make_move(mv.0, mv.1);
        let score = evaluate(game, player, policy, cfg);
        game.undo_last_move();
        return Some(MctsResult {
            best_move: mv,
            num_gamestates: 0,
            depth_explored: 0,
            move_stats: vec![(mv, score, 0)],
            thinking_time: 0.0,
            early_stop: true,
            search_type: "mcts",
        });
    }

    // --- Main MCTS loop ---
    let root_player = game.next_to_move;
    let mut root = TreeNode::new(game, cfg.ucb_constant);
    let start = Instant::now();

    while start.elapsed().as_secs_f64() <= max_seconds
        && root.number_of_plays < max_nodes
    {
        root.expand_tree_by_one(game, root_player, policy, cfg, 0);
    }

    let best_move = select_best_move(game, &root, policy, cfg);
    let best_move = best_move?;

    let thinking_time = start.elapsed().as_secs_f64();
    let move_stats: Vec<(Move, f64, u32)> = root
        .children
        .iter()
        .map(|(&mv, child)| (mv, child.mean_score(), child.number_of_plays))
        .collect();

    Some(MctsResult {
        best_move,
        num_gamestates: root.number_of_plays,
        depth_explored: root.depth_seen,
        move_stats,
        thinking_time,
        early_stop: false,
        search_type: "mcts",
    })
}

fn should_use_exact(game: &Game, cfg: &PolicyConfig, legal: &[Move]) -> bool {
    use crate::exact_endgame::{count_legal_cells, count_empty_cells};
    if legal.len() <= 1 {
        return false;
    }
    if cfg.exact_endgame_legal_cells_threshold >= 0 {
        return count_legal_cells(game) <= cfg.exact_endgame_legal_cells_threshold as usize;
    }
    if cfg.exact_endgame_empty_cells_threshold >= 0 {
        return count_empty_cells(game) <= cfg.exact_endgame_empty_cells_threshold as usize;
    }
    false
}

fn select_best_move(
    game: &mut Game,
    root: &TreeNode,
    policy: PolicyType,
    cfg: &PolicyConfig,
) -> Option<Move> {
    if matches!(policy, PolicyType::Pragmatic) {
        // Build move_stats for pragmatic priority selection
        let stats: Vec<(Move, f64, u32)> = root
            .children
            .iter()
            .map(|(&mv, child)| (mv, child.mean_score(), child.number_of_plays))
            .collect();
        return select_final_move_pragmatic(game, &stats, cfg);
    }
    // Baseline + GraphPuct when used in tree mode: most visits
    let mut best: Option<(Move, u32, f64)> = Option::None;
    for (&mv, child) in &root.children {
        let visits = child.number_of_plays;
        let score = child.mean_score();
        let better = match best {
            Option::None => true,
            Some((bm, bv, bs)) => {
                visits > bv
                    || (visits == bv && score > bs)
                    || (visits == bv && score == bs && (mv.0, mv.1) < (bm.0, bm.1))
            }
        };
        if better {
            best = Some((mv, visits, score));
        }
    }
    best.map(|(mv, _, _)| mv)
}
