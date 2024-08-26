import boto3

# AWS client functions most likely:
#
# - get_cost_and_usage
# - get_cost_categories
# - get_tags
# - list_cost_allocation_tags
#


def query_aws_cost_explorer():
    aws_ce_client = boto3.client("ce")

    # ref: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ce/client/get_cost_and_usage.html#get-cost-and-usage
    response = aws_ce_client.get_cost_and_usage(
        Metrics=["UnblendedCost"],
        Granularity="DAILY",
        TimePeriod={
            "Start": "2024-07-01",
            "End": "2024-08-01",
        },
        Filter={
            "Dimensions": {
                # RECORD_TYPE is also called Charge type. By filtering on this
                # we avoid results related to credits, tax, etc.
                "Key": "RECORD_TYPE",
                "Values": ["Usage"],
            },
        },
        GroupBy=[
            {
                "Type": "DIMENSION",
                "Key": "SERVICE",
            },
        ],
    )
    return response["ResultsByTime"]


# Granularity:
#
# - HOURLY, DAILY, or MONTHLY
#
# - Hourly resolution is only available for the last two days, so we'll use a
#   daily resolution which is available for the last 13 months.
#
#
#
# Metrics:
#
# - Valid choices:
#   - AmortizedCost
#   - BlendedCosts
#   - NetAmortizedCost
#   - NetUnblendedCost
#   - NormalizedUsageAmount
#   - UnblendedCosts
#   - UsageQuantity
#
# - UnblendedCosts is the default metric presented in the web console, it
#   represents costs for an individual AWS account. When combining costs in an
#   organization, 1 + 1 <= 2, because the accounts cumulative use can reduce
#   rates.
#
# - We'll focus on UnblendedCosts though, because makes the service cost
#   decoupled from other cloud accounts usage.
#
# Filter:
#
# - RECORD_TYPE is what's named Charge type in the web console, and looking at
#   "Usage" only that helps us avoid responses related to credits, tax, etc.
#
# - Dimensions:
#   - AZ
#   - INSTANCE_TYPE
#   - LINKED_ACCOUNT
#   - LINKED_ACCOUNT_NAME
#   - OPERATION
#   - PURCHASE_TYPE
#   - REGION
#   - SERVICE
#   - SERVICE_CODE
#   - USAGE_TYPE
#   - USAGE_TYPE_GROUP
#   - RECORD_TYPE
#   - OPERATING_SYSTEM
#   - TENANCY
#   - SCOPE
#   - PLATFORM
#   - SUBSCRIPTION_ID
#   - LEGAL_ENTITY_NAME
#   - DEPLOYMENT_OPTION
#   - DATABASE_ENGINE
#   - CACHE_ENGINE
#   - INSTANCE_TYPE_FAMILY
#   - BILLING_ENTITY
#   - RESERVATION_ID
#   - RESOURCE_ID (available only for the last 14 days of usage)
#   - RIGHTSIZING_TYPE
#   - SAVINGS_PLANS_TYPE
#   - SAVINGS_PLAN_ARN
#   - PAYMENT_OPTION
#   - AGREEMENT_END_DATE_TIME_AFTER
#   - AGREEMENT_END_DATE_TIME_BEFORE
#   - INVOICING_ENTITY
#   - ANOMALY_TOTAL_IMPACT_ABSOLUTE
#   - ANOMALY_TOTAL_IMPACT_PERCENTAGE
# - Tags:
#   - Refers to Cost Allocation Tags.
# - CostCategories:
#   - Can include Cost Allocation Tags, but also references various services
#     etc.
#
# GroupBy
#
# - Can be an array with up to two string elements, being either:
#   - DIMENSION
#   - TAG
#   - COST_CATEGORY
#

# Description of Grafana panels wanted by Yuvi:
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
