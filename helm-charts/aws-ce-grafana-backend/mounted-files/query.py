"""
Queries to AWS Cost Explorer to get different kinds of cost data.
"""

import functools
import logging

import boto3

from .cache import ttl_lru_cache
from .const import (
    FILTER_ATTRIBUTABLE_COSTS,
    FILTER_USAGE_COSTS,
    GRANULARITY_DAILY,
    GROUP_BY_HUB_TAG,
    GROUP_BY_SERVICE_DIMENSION,
    METRICS_UNBLENDED_COST,
    SERVICE_COMPONENT_MAP,
)

logger = logging.getLogger(__name__)
aws_ce_client = boto3.client("ce")


@functools.cache
def _get_component_name(service_name):
    if service_name in SERVICE_COMPONENT_MAP:
        return SERVICE_COMPONENT_MAP[service_name]
    else:
        # only printed once per service name thanks to memoization
        logger.warning(f"Service '{service_name}' not categorized as a component yet")
        return "other"


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


@ttl_lru_cache(seconds_to_live=3600)
def query_hub_names(from_date, to_date):
    # ref: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ce/client/get_tags.html
    response = aws_ce_client.get_tags(
        TimePeriod={"Start": from_date, "End": to_date},
        TagKey="2i2c:hub-name",
    )
    # response looks like...
    #
    # {
    #     "Tags": ["", "prod", "staging", "workshop"],
    #     "ReturnSize": 4,
    #     "TotalSize": 4,
    #     "ResponseMetadata": {
    #         "RequestId": "23736d32-9929-4b6a-8c4f-d80b1487ed37",
    #         "HTTPStatusCode": 200,
    #         "HTTPHeaders": {
    #             "date": "Fri, 20 Sep 2024 12:42:13 GMT",
    #             "content-type": "application/x-amz-json-1.1",
    #             "content-length": "70",
    #             "connection": "keep-alive",
    #             "x-amzn-requestid": "23736d32-9929-4b6a-8c4f-d80b1487ed37",
    #             "cache-control": "no-cache",
    #         },
    #         "RetryAttempts": 0,
    #     },
    # }
    #
    # The empty string is replaced with "shared"
    #
    hub_names = [t or "shared" for t in response["Tags"]]
    return hub_names


@ttl_lru_cache(seconds_to_live=3600)
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


@ttl_lru_cache(seconds_to_live=3600)
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


@ttl_lru_cache(seconds_to_live=3600)
def query_total_costs_per_component(from_date, to_date, hub_name=None):
    """
    A query with processing of the response tailored query to report total costs
    per component - a grouping of services.

    If a hub_name is specified, component costs are filtered to only consider
    costs directly attributable to the hub name.
    """
    filter = {
        "And": [
            FILTER_USAGE_COSTS,
            FILTER_ATTRIBUTABLE_COSTS,
        ]
    }
    if hub_name == "shared":
        filter["And"].append(
            {
                "Tags": {
                    "Key": "2i2c:hub-name",
                    "MatchOptions": ["ABSENT"],
                },
            }
        )
    elif hub_name:
        filter["And"].append(
            {
                "Tags": {
                    "Key": "2i2c:hub-name",
                    "Values": [hub_name],
                    "MatchOptions": ["EQUALS"],
                },
            }
        )

    response = query_aws_cost_explorer(
        metrics=[METRICS_UNBLENDED_COST],
        granularity=GRANULARITY_DAILY,
        from_date=from_date,
        to_date=to_date,
        filter=filter,
        group_by=[GROUP_BY_SERVICE_DIMENSION],
    )

    # response["ResultsByTime"] is a list with entries looking like this...
    #
    # [
    #     {
    #         "TimePeriod": {"Start": "2024-08-30", "End": "2024-08-31"},
    #         "Total": {},
    #         "Groups": [
    #             {
    #                 "Keys": ["AWS Backup"],
    #                 "Metrics": {
    #                     "UnblendedCost": {"Amount": "2.4763369432", "Unit": "USD"}
    #                 },
    #             },
    #             {
    #                 "Keys": ["EC2 - Other"],
    #                 "Metrics": {
    #                     "UnblendedCost": {"Amount": "3.2334814259", "Unit": "USD"}
    #                 },
    #             },
    #             {
    #                 "Keys": ["Amazon Elastic Compute Cloud - Compute"],
    #                 "Metrics": {
    #                     "UnblendedCost": {"Amount": "12.5273401469", "Unit": "USD"}
    #                 },
    #             },
    #             {
    #                 "Keys": ["Amazon Elastic Container Service for Kubernetes"],
    #                 "Metrics": {"UnblendedCost": {"Amount": "2.4", "Unit": "USD"}},
    #             },
    #             {
    #                 "Keys": ["Amazon Elastic File System"],
    #                 "Metrics": {
    #                     "UnblendedCost": {"Amount": "9.4433542756", "Unit": "USD"}
    #                 },
    #             },
    #             {
    #                 "Keys": ["Amazon Elastic Load Balancing"],
    #                 "Metrics": {
    #                     "UnblendedCost": {"Amount": "0.6147035689", "Unit": "USD"}
    #                 },
    #             },
    #             {
    #                 "Keys": ["Amazon Simple Storage Service"],
    #                 "Metrics": {
    #                     "UnblendedCost": {"Amount": "0.1094078516", "Unit": "USD"}
    #                 },
    #             },
    #             {
    #                 "Keys": ["Amazon Virtual Private Cloud"],
    #                 "Metrics": {
    #                     "UnblendedCost": {"Amount": "0.24867778", "Unit": "USD"}
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
    #         "date": "2024-08-30",
    #         "cost": "12.19",
    #         "name": "home storage",
    #     },
    # ]
    #
    processed_response = []
    for e in response["ResultsByTime"]:
        # coalesce service costs to component costs
        component_costs = {}
        for g in e["Groups"]:
            service_name = g["Keys"][0]
            name = _get_component_name(service_name)
            cost = float(g["Metrics"]["UnblendedCost"]["Amount"])
            component_costs[name] = component_costs.get(name, 0.0) + cost

        processed_response.extend(
            [
                {
                    "date": e["TimePeriod"]["Start"],
                    "cost": f"{cost:.2f}",
                    "name": name,
                }
                for name, cost in component_costs.items()
            ]
        )

    return processed_response
