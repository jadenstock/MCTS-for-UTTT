from invoke import task

@task
def run_server(c):
    """Run the Flask server."""
    c.run("python src/uttt_ai/flask_server.py")