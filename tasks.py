from invoke import task

@task
def run_server(c, port=5000):
    """Run the Flask server.

    Args:
        port (int): Port number to run the server on (default: 5000)
    """
    c.run(f"python src/flask_server.py --port {port}")