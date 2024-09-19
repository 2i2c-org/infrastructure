"""
Queries to AWS Cost Explorer to get different kinds of cost data.
"""

import boto3

aws_ce_client = boto3.client("ce")


def query_total_cost(cluster_name, from_date, to_date):
    results = query_aws_cost_explorer(cluster_name, from_date, to_date)
    return results


def query_aws_cost_explorer(cluster_name, from_date, to_date):
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
                                "Values": [cluster_name],
                                "MatchOptions": ["EQUALS"],
                            },
                        },
                        {
                            "Tags": {
                                "Key": f"kubernetes.io/cluster/{cluster_name}",
                                "Values": ["owned"],
                                "MatchOptions": ["EQUALS"],
                            },
                        },
                        {
                            "Tags": {
                                "Key": "2i2c.org/cluster-name",
                                "Values": [cluster_name],
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
        # FIXME: Add this or something similar back when focusing on something
        #        beyond just the total daily costs.
        #
        # GroupBy=[
        #     {
        #         "Type": "DIMENSION",
        #         "Key": "SERVICE",
        #     },
        # ],
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
    processed_response = [
        {
            "date": e["TimePeriod"]["Start"],
            "cost": f'{float(e["Total"]["UnblendedCost"]["Amount"]):.2f}',
        }
        for e in response["ResultsByTime"]
    ]
    return processed_response
