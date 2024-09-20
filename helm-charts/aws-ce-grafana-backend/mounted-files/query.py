"""
Queries to AWS Cost Explorer to get different kinds of cost data.
"""

import boto3

from .const import (
    FILTER_ATTRIBUTABLE_COSTS,
    FILTER_USAGE_COSTS,
    GRANULARITY_DAILY,
    GROUP_BY_HUB_TAG,
    METRICS_UNBLENDED_COST,
)

aws_ce_client = boto3.client("ce")


def query_aws_cost_explorer(metrics, granularity, from_date, to_date, filter, group_by):
    """
    Function meant to be responsible for making the API call and handling
    pagination etc. Currently pagination isn't handled.
    """
    # ref: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ce/client/get_cost_and_usage.html#get-cost-and-usage
    response = aws_ce_client.get_cost_and_usage(
        Metrics=metrics,
        Granularity=granularity,
        TimePeriod={"Start": from_date, "End": to_date},
        Filter=filter,
        GroupBy=group_by,
    )
    return response


def query_total_costs(from_date, to_date):
    """
    A query with processing of the response tailored query to report hub
    independent total costs.
    """
    response = query_aws_cost_explorer(
        metrics=[METRICS_UNBLENDED_COST],
        granularity=GRANULARITY_DAILY,
        from_date=from_date,
        to_date=to_date,
        filter={
            "And": [
                FILTER_USAGE_COSTS,
                FILTER_ATTRIBUTABLE_COSTS,
            ]
        },
        group_by=[],
    )

    # response["ResultsByTime"] is a list with entries looking like this...
    #
    # [
    #     {
    #         "Estimated": false,
    #         "Groups": [],
    #         "TimePeriod": {
    #             "End": "2024-07-28",
    #             "Start": "2024-07-27",
    #         },
    #         "Total": {
    #             "UnblendedCost": {
    #                 "Amount": "23.3110299724",
    #                 "Unit": "USD",
    #             },
    #         },
    #     },
    #     # ...
    # ]
    #
    # processed_response is a list with entries looking like this...
    #
    # [
    #     {
    #         "date":"2024-08-30",
    #         "cost":"12.19",
    #     },
    # ]
    #
    processed_response = [
        {
            "date": e["TimePeriod"]["Start"],
            "cost": f'{float(e["Total"]["UnblendedCost"]["Amount"]):.2f}',
        }
        for e in response["ResultsByTime"]
    ]
    return processed_response


def query_total_costs_per_hub(from_date, to_date):
    """
    A query with processing of the response tailored query to report total costs
    per hub, where costs not attributed to a specific hub is listed under
    'shared'.
    """
    response = query_aws_cost_explorer(
        metrics=[METRICS_UNBLENDED_COST],
        granularity=GRANULARITY_DAILY,
        from_date=from_date,
        to_date=to_date,
        filter={
            "And": [
                FILTER_USAGE_COSTS,
                FILTER_ATTRIBUTABLE_COSTS,
            ]
        },
        group_by=[
            GROUP_BY_HUB_TAG,
        ],
    )

    # response["ResultsByTime"] is a list with entries looking like this...
    #
    # [
    #     {
    #         "TimePeriod": {"Start": "2024-08-30", "End": "2024-08-31"},
    #         "Total": {},
    #         "Groups": [
    #             {
    #                 "Keys": ["2i2c:hub-name$"],
    #                 "Metrics": {
    #                     "UnblendedCost": {"Amount": "12.1930361882", "Unit": "USD"}
    #                 },
    #             },
    #             {
    #                 "Keys": ["2i2c:hub-name$prod"],
    #                 "Metrics": {
    #                     "UnblendedCost": {"Amount": "18.662514854", "Unit": "USD"}
    #                 },
    #             },
    #             {
    #                 "Keys": ["2i2c:hub-name$staging"],
    #                 "Metrics": {
    #                     "UnblendedCost": {"Amount": "0.000760628", "Unit": "USD"}
    #                 },
    #             },
    #             {
    #                 "Keys": ["2i2c:hub-name$workshop"],
    #                 "Metrics": {
    #                     "UnblendedCost": {"Amount": "0.1969903219", "Unit": "USD"}
    #                 },
    #             },
    #         ],
    #         "Estimated": False,
    #     },
    # ]
    #
    # processed_response is a list with entries looking like this...
    #
    # [
    #     {
    #         "date":"2024-08-30",
    #         "cost":"12.19",
    #         "name":"shared",
    #     },
    # ]
    #
    processed_response = []
    for e in response["ResultsByTime"]:
        processed_response.extend(
            [
                {
                    "date": e["TimePeriod"]["Start"],
                    "cost": f'{float(g["Metrics"]["UnblendedCost"]["Amount"]):.2f}',
                    "name": g["Keys"][0].split("$", maxsplit=1)[1] or "shared",
                }
                for g in e["Groups"]
            ]
        )

    return processed_response
