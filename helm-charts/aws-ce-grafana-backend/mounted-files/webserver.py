from flask import Flask

from .aws import query_aws_cost_explorer

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/health/ready")
def ready():
    return ("", 204)


@app.route("/aws")
def aws():
    return query_aws_cost_explorer()
