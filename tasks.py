from invoke import task

@task
def run_server(c, port=5000):
    """Run the Flask server.

    Args:
        port (int): Port number to run the server on (default: 5000)
    """
    c.run(f"python src/flask_server.py --port {port}")


@task
def self_play(c, agent1="default", agent2="default", compute_time=5):
    """Run a self-play game between two agents.

    Args:
        agent1 (str): Agent ID for player 'x' (default: 'default')
        agent2 (str): Agent ID for player 'o' (default: 'default')
        compute_time (int): Compute time per move in seconds (default: 5)
    """
    env = {"PYTHONPATH": "src"}
    c.run(
        f"python -m core.self_play --agent1 {agent1} --agent2 {agent2} --compute_time {compute_time}",
        env=env
    )

@task
def validate_config(c, agent="default"):
    """
    Validate the configuration for the specified agent.

    Args:
        agent (str): Agent id to validate (default: "default")
    """
    env = {"PYTHONPATH": "src"}
    c.run(
        f"python -c \"from utils.game_score_utils import validate_config; validate_config(agent_id='{agent}')\"",
        env=env
    )


@task
def benchmark(c, agent_a="default", agent_b="aggressive", games=20, compute_time=60, node_limit=200, opening_random_plies=2, seed=42):
    """Run reproducible self-play benchmark between two agents."""
    env = {"PYTHONPATH": "src"}
    c.run(
        "python -m core.benchmark "
        f"--agent-a {agent_a} "
        f"--agent-b {agent_b} "
        f"--games {games} "
        f"--compute-time {compute_time} "
        f"--node-limit {node_limit} "
        f"--opening-random-plies {opening_random_plies} "
        f"--seed {seed}",
        env=env,
    )


@task
def benchmark_enqueue(
    c,
    agent_a="default",
    agent_b="graph_puct_v1",
    games=1,
    compute_time=1,
    node_limit=200,
    opening_random_plies=2,
    seed=42,
    save_dir="data/bot_games",
    progress_log_interval_moves=5,
):
    """Enqueue one benchmark job into the local queue."""
    env = {"PYTHONPATH": "src"}
    c.run(
        "python -m core.benchmark_jobs "
        "enqueue "
        f"--agent-a {agent_a} "
        f"--agent-b {agent_b} "
        f"--games {games} "
        f"--compute-time {compute_time} "
        f"--node-limit {node_limit} "
        f"--opening-random-plies {opening_random_plies} "
        f"--seed {seed} "
        f"--save-dir {save_dir} "
        f"--progress-log-interval-moves {progress_log_interval_moves}",
        env=env,
    )


@task
def benchmark_jobs(c, status="", limit=100):
    """List benchmark queue jobs."""
    env = {"PYTHONPATH": "src"}
    status_arg = f"--status {status} " if status else ""
    c.run(
        "python -m core.benchmark_jobs "
        f"list {status_arg}"
        f"--limit {limit}",
        env=env,
    )


@task
def benchmark_cancel(c, job_id):
    """Cancel a queued or running benchmark job by id."""
    env = {"PYTHONPATH": "src"}
    c.run(
        "python -m core.benchmark_jobs "
        f"cancel --job-id {job_id}",
        env=env,
    )


@task
def benchmark_runner(c, workers=3, poll_interval=1.0, status_interval=10.0):
    """Run benchmark queue workers until interrupted."""
    env = {"PYTHONPATH": "src"}
    c.run(
        "python -m core.benchmark_runner "
        f"--workers {workers} "
        f"--poll-interval {poll_interval} "
        f"--status-interval {status_interval}",
        env=env,
    )
