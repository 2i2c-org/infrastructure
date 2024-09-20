"""
Queries to AWS Cost Explorer to get different kinds of cost data.
"""

import os

import boto3

# Environment variables based config isn't great, see fixme comment in
# values.yaml under the software configuration heading
CLUSTER_NAME = os.environ["AWS_CE_GRAFANA_BACKEND__CLUSTER_NAME"]

aws_ce_client = boto3.client("ce")


def query_total_cost(from_date, to_date):
    results = query_aws_cost_explorer(from_date, to_date)
    return results


def query_aws_cost_explorer(from_date, to_date):
    # ref: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ce/client/get_cost_and_usage.html#get-cost-and-usage
    response = aws_ce_client.get_cost_and_usage(
        # Metrics:
        #
        #   UnblendedCosts represents costs for an individual AWS account. It is
        #   the default metric in the AWS web console. BlendedCosts represents
        #   the potentially reduced costs stemming from having multiple AWS
        #   accounts in an organization the collectively could enter better
        #   pricing tiers.
        #
        Metrics=["UnblendedCost"],
        # Granularity:
        #
        #   HOURLY granularity is only available for the last two days, while
        #   DAILY is available for the last 13 months.
        #
        Granularity="DAILY",
        TimePeriod={
            "Start": from_date,
            "End": to_date,
        },
        Filter={
            "And": [
                {
                    "Dimensions": {
                        # RECORD_TYPE is also called Charge type. By filtering on this
                        # we avoid results related to credits, tax, etc.
                        "Key": "RECORD_TYPE",
                        "Values": ["Usage"],
                    },
                },
                {
                    # ref: https://github.com/2i2c-org/infrastructure/issues/4787#issue-2519110356
                    "Or": [
                        {
                            "Tags": {
                                "Key": "alpha.eksctl.io/cluster-name",
                                "Values": [CLUSTER_NAME],
                                "MatchOptions": ["EQUALS"],
                            },
                        },
                        {
                            "Tags": {
                                "Key": f"kubernetes.io/cluster/{CLUSTER_NAME}",
                                "Values": ["owned"],
                                "MatchOptions": ["EQUALS"],
                            },
                        },
                        {
                            "Tags": {
                                "Key": "2i2c.org/cluster-name",
                                "Values": [CLUSTER_NAME],
                                "MatchOptions": ["EQUALS"],
                            },
                        },
                        {
                            "Not": {
                                "Tags": {
                                    "Key": "2i2c:hub-name",
                                    "MatchOptions": ["ABSENT"],
                                },
                            },
                        },
                        {
                            "Not": {
                                "Tags": {
                                    "Key": "2i2c:node-purpose",
                                    "MatchOptions": ["ABSENT"],
                                },
                            },
                        },
                    ],
                },
            ]
        },
        GroupBy=[
            {
                "Type": "TAG",
                "Key": "2i2c:hub-name",
            },
        ],
    )

    print(response)

    # response["ResultsByTime"] is a list with entries looking like this if
    # GroupBy isn't specified...
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
    # response["ResultsByTime"] is a list with entries looking like this if
    # GroupBy is specified...
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
    processed_response = [
        {
            "date": e["TimePeriod"]["Start"],
            "cost": f'{float(e["Total"]["UnblendedCost"]["Amount"]):.2f}',
        }
        for e in response["ResultsByTime"]
    ]
    return processed_response
