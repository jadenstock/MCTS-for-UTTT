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