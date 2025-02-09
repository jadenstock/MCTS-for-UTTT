from invoke import task

@task
def run_server(c):
    """Run the Flask server."""
    c.run("python src/flask_server.py")