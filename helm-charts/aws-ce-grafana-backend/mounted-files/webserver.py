from datetime import date, datetime, timedelta, timezone

from flask import Flask, request

from .query import query_total_costs, query_total_costs_per_hub

app = Flask(__name__)


def parse_from_to_in_query_params():
    """
    Parse "from" and "to" query parameters, expected to arrive as YYYY-MM-DD
    strings.

    # FIXME: Avoid...
    #        botocore.exceptions.ClientError: An error occurred (ValidationException) when calling the GetCostAndUsage operation: end date past the beginning of next month

    - "to" defaults to current date (UTC)
    - "from" defaults to 30 days before what to is set to
    """
    if request.args.get("to"):
        to_dt = date.fromisoformat(request.args["to"])
    else:
        to_dt = datetime.now(timezone.utc).date()
    if request.args.get("from"):
        from_dt = date.fromisoformat(request.args["from"])
    else:
        from_dt = to_dt - timedelta(days=30)

    # the end date gets excluded, so add one day to get it included
    to_dt += timedelta(days=1)

    # format back to YYYY-MM-DD strings
    from_date = from_dt.strftime("%Y-%m-%d")
    to_date = to_dt.strftime("%Y-%m-%d")

    return from_date, to_date


@app.route("/health/ready")
def ready():
    return ("", 204)


@app.route("/total-costs")
def total_costs():
    from_date, to_date = parse_from_to_in_query_params()

    return query_total_costs(from_date, to_date)


@app.route("/total-costs-per-hub")
def total_costs_per_hub():
    from_date, to_date = parse_from_to_in_query_params()

    return query_total_costs_per_hub(from_date, to_date)
