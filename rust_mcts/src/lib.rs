mod eval;
mod exact_endgame;
mod game;
mod graph_puct;
mod mcts_core;
mod policy;

use std::collections::HashMap;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};

use eval::PolicyConfig;
use game::game_from_state;
use policy::PolicyType;

// ---------------------------------------------------------------------------
// PyO3 0.22 helpers
// ---------------------------------------------------------------------------

fn py_move_tuple<'py>(py: Python<'py>, mv: (u8, u8)) -> Bound<'py, PyTuple> {
    PyTuple::new_bound(py, [mv.0 as u64, mv.1 as u64])
}

fn build_mcts_metadata<'py>(
    py: Python<'py>,
    result: &mcts_core::MctsResult,
) -> PyResult<Bound<'py, PyDict>> {
    let d = PyDict::new_bound(py);
    d.set_item("num_gamestates", result.num_gamestates)?;
    d.set_item("depth_explored", result.depth_explored)?;
    d.set_item("thinking_time", result.thinking_time)?;
    d.set_item("early_stop", result.early_stop)?;
    d.set_item("search_type", result.search_type)?;

    let mut sorted = result.move_stats.clone();
    sorted.sort_by(|a, b| {
        b.1.partial_cmp(&a.1)
            .unwrap_or(std::cmp::Ordering::Equal)
            .then(b.2.cmp(&a.2))
    });

    let moves_list = PyList::empty_bound(py);
    for (mv, score, plays) in &sorted {
        let entry = PyTuple::new_bound(py, vec![
            py_move_tuple(py, *mv).into_py(py),
            score.into_py(py),
            plays.into_py(py),
        ]);
        moves_list.append(entry)?;
    }
    d.set_item("moves", moves_list)?;
    Ok(d)
}

fn build_graph_puct_metadata<'py>(
    py: Python<'py>,
    result: &graph_puct::GraphPuctResult,
) -> PyResult<Bound<'py, PyDict>> {
    let d = PyDict::new_bound(py);
    d.set_item("num_gamestates", result.num_gamestates)?;
    d.set_item("depth_explored", result.depth_explored)?;
    d.set_item("thinking_time", result.thinking_time)?;
    d.set_item("early_stop", result.early_stop)?;
    d.set_item("search_type", result.search_type)?;

    let mut sorted = result.move_stats.clone();
    sorted.sort_by(|a, b| {
        b.2.cmp(&a.2).then(
            b.1.unwrap_or(f64::NEG_INFINITY)
                .partial_cmp(&a.1.unwrap_or(f64::NEG_INFINITY))
                .unwrap_or(std::cmp::Ordering::Equal),
        )
    });

    let moves_list = PyList::empty_bound(py);
    for (mv, score, plays) in &sorted {
        let score_obj: PyObject = match score {
            Some(s) => s.into_py(py),
            None => py.None(),
        };
        let entry = PyTuple::new_bound(py, vec![
            py_move_tuple(py, *mv).into_py(py),
            score_obj,
            plays.into_py(py),
        ]);
        moves_list.append(entry)?;
    }
    d.set_item("moves", moves_list)?;
    Ok(d)
}

// ---------------------------------------------------------------------------
// Python-callable: run_mcts
// ---------------------------------------------------------------------------

/// Run UCB1 tree MCTS (baseline or pragmatic policy).
///
/// Args:
///   boards          - list[list[str]]   9 mini-boards × 9 cells ("", "x", "o")
///   mini_winners    - list[str]         winner of each mini-board
///   global_winner   - str
///   next_to_move    - "x" | "o"
///   last_cell       - int  (-1 = no previous move)
///   config          - dict[str, float]  policy / search knobs
///   policy_type     - "baseline" | "pragmatic"
///   max_seconds     - float
///   max_nodes       - int
///   include_metadata - bool
///
/// Returns [board_idx, cell_idx, metadata_dict]  or  (board_idx, cell_idx).
#[pyfunction]
#[pyo3(signature = (boards, mini_winners, global_winner, next_to_move, last_cell,
                    config, policy_type, max_seconds, max_nodes, include_metadata=true))]
fn run_mcts(
    py: Python<'_>,
    boards: Vec<Vec<String>>,
    mini_winners: Vec<String>,
    global_winner: String,
    next_to_move: String,
    last_cell: i32,
    config: HashMap<String, f64>,
    policy_type: String,
    max_seconds: f64,
    max_nodes: u32,
    include_metadata: bool,
) -> PyResult<PyObject> {
    let mut game = game_from_state(
        &boards,
        &mini_winners,
        &global_winner,
        &next_to_move,
        last_cell,
    );
    let cfg = PolicyConfig::from_map(&config);
    let policy = PolicyType::from_str(&policy_type);

    let result =
        mcts_core::run_mcts(&mut game, policy, &cfg, max_seconds, max_nodes, include_metadata);
    let result = match result {
        Some(r) => r,
        None => return Ok(py.None()),
    };

    if !include_metadata {
        return Ok(PyTuple::new_bound(
            py,
            [result.best_move.0 as u64, result.best_move.1 as u64],
        )
        .into_py(py));
    }

    let meta = build_mcts_metadata(py, &result)?;
    Ok(PyList::new_bound(py, vec![
        (result.best_move.0 as u64).into_py(py),
        (result.best_move.1 as u64).into_py(py),
        meta.into_py(py),
    ])
    .into_py(py))
}

// ---------------------------------------------------------------------------
// Python-callable: run_graph_puct
// ---------------------------------------------------------------------------

#[pyfunction]
#[pyo3(signature = (boards, mini_winners, global_winner, next_to_move, last_cell,
                    config, max_seconds, max_nodes, include_metadata=true))]
fn run_graph_puct(
    py: Python<'_>,
    boards: Vec<Vec<String>>,
    mini_winners: Vec<String>,
    global_winner: String,
    next_to_move: String,
    last_cell: i32,
    config: HashMap<String, f64>,
    max_seconds: f64,
    max_nodes: u32,
    include_metadata: bool,
) -> PyResult<PyObject> {
    let mut game = game_from_state(
        &boards,
        &mini_winners,
        &global_winner,
        &next_to_move,
        last_cell,
    );
    let cfg = PolicyConfig::from_map(&config);

    let result =
        graph_puct::run_graph_puct(&mut game, &cfg, max_seconds, max_nodes, include_metadata);
    let result = match result {
        Some(r) => r,
        None => return Ok(py.None()),
    };

    if !include_metadata {
        return Ok(PyTuple::new_bound(
            py,
            [result.best_move.0 as u64, result.best_move.1 as u64],
        )
        .into_py(py));
    }

    let meta = build_graph_puct_metadata(py, &result)?;
    Ok(PyList::new_bound(py, vec![
        (result.best_move.0 as u64).into_py(py),
        (result.best_move.1 as u64).into_py(py),
        meta.into_py(py),
    ])
    .into_py(py))
}

// ---------------------------------------------------------------------------
// Module
// ---------------------------------------------------------------------------

#[pymodule]
fn rust_mcts(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(run_mcts, m)?)?;
    m.add_function(wrap_pyfunction!(run_graph_puct, m)?)?;
    Ok(())
}
