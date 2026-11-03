"""API Flask du Triangulator."""

from flask import Flask

app = Flask(__name__)


@app.route("/triangulation/<pointset_id>", methods=["GET"])
def get_triangulation(pointset_id: str):
    """Renvoie la triangulation du PointSet en binaire."""
    raise NotImplementedError


if __name__ == "__main__":
    app.run(port=5000)
