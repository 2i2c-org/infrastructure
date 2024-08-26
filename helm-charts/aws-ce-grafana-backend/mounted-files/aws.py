import boto3

# AWS client functions most likely:
#
# - get_cost_and_usage
# - get_cost_categories
# - get_tags
# - list_cost_allocation_tags
#
aws_ce_client = boto3.client("ce")


def query_total_cost(from_date, to_date):
    results = query_aws_cost_explorer(from_date, to_date)
    return results


def query_aws_cost_explorer(from_date, to_date):
    # ref: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ce/client/get_cost_and_usage.html#get-cost-and-usage
    response = aws_ce_client.get_cost_and_usage(
        # Metrics:
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
            "Dimensions": {
                # RECORD_TYPE is also called Charge type. By filtering on this
                # we avoid results related to credits, tax, etc.
                "Key": "RECORD_TYPE",
                "Values": ["Usage"],
            },
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
    return response["ResultsByTime"]


# Description of Grafana panels requested by Yuvi:
# ref: https://github.com/2i2c-org/infrastructure/issues/4453#issuecomment-2298076415
#
# Currently our AWS tag 2i2c:hub-name is only capturing a fraction of the costs,
# so initially only the following panels are easy to work on.
#
# - total cost (4)
# - total cost per component (2)
#
# The following panels are dependent on the 2i2c:hub-name tag though.
#
# - total cost per hub (1)
# - total cost per component, repeated per hub (3)
#
# Summarized notes about user facing labels:
#
# - fixed:
#   - core nodepool
#   - any PV needed for support chart or hub databases
#   - Kubernetes master API
#   - load balancer services
# - compute:
#   - disks
#   - networking
#   - gpus
# - home storage:
#   - backups
# - object storage:
#   - tagged buckets
#   - not counting requester pays
# - total:
#   - all 2i2c managed infra
#
# Working against cost tags directly or cost categories
#
# Cost categories vs Cost allocation tags
#
# - It seems cost categories could be suitable to group misc data under
#   categories, and split things like core node pool.
# - I think its worth exploring if we could offload all complexity about user
#   facing labels etc by using cost categories to group and label costs.
#
