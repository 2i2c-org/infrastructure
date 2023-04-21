import re
from collections import defaultdict
from datetime import datetime

from google.cloud import bigquery

from ..grafana.grafana_utils import get_cluster_prometheus


def get_cluster_costs(cluster, start_month, end_month):
    tenancy = cluster.get("tenancy", "dedicated")
    if tenancy == "shared":
        return get_shared_hub_costs(cluster, start_month, end_month)
    elif tenancy == "dedicated":
        return get_dedicated_cluster_costs(cluster, start_month, end_month)
    return []


def get_dedicated_cluster_costs(cluster, start_month, end_month):
    """Return monthly costs for a dedicated cluster for a range of months

    Args:
        cluster (dict): parsed cluster.yaml
        start_month (str): Starting month (as YYYY-MM)
        end_month (str): End month (as YYYY-MM)

    Returns:
        rows (list of costs per project)
    """

    # TODO(pnasrat): Pass client in or encapsulate in an class?
    client = bigquery.Client()

    # TODO(pnasrat): we are using GCP project name not cluster name.
    cluster_project_name = cluster["gcp"]["project"]

    bq = cluster["gcp"]["billing"]["bigquery"]

    # WARN: We are using string interpolation here to construct a sql-like query, which
    # IS GENERALLY VERY VERY BAD AND NO GOOD AND WE SHOULD NOT DO IT NO EVER.
    # HOWEVER, I can't seem to find a way to parameterize the *table name* as we must do here,
    # rather than just query parameters. So we *very* carefully construct the name of the table here,
    # and use that in the query. In addition, we allow-list the characters available to the table name as
    # well - and fail hard if something is fishy. This shouldn't really be a problem, as we control the
    # input to this function (via our YAML file). However, SQL Injections are likely to happen in places
    # where you least expect them to happen, so the extra layer of protection is nice.
    table_name = f'{bq["project"]}.{bq["dataset"]}.gcp_billing_export_resource_v1_{bq["billing_id"].replace("-", "_")}'
    # Make sure the table name only has alphanumeric characters, _ and -
    assert re.match(r"^[a-zA-Z0-9._-]+$", table_name)
    query = f"""
        SELECT
        invoice.month as month,
        project.id as project,
        (SUM(CAST(cost AS NUMERIC))
            + SUM(IFNULL((SELECT SUM(CAST(c.amount AS NUMERIC))
                        FROM UNNEST(credits) AS c), 0)))
            AS total_with_credits
        FROM `{table_name}`
        WHERE invoice.month >= @start_month
              AND invoice.month <= @end_month
              AND project.id = @project
        GROUP BY 1, 2
        ORDER BY invoice.month ASC
        ;
        """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_month", "STRING", start_month),
            bigquery.ScalarQueryParameter("end_month", "STRING", end_month),
            bigquery.ScalarQueryParameter("project", "STRING", cluster_project_name),
        ]
    )

    result = client.query(query, job_config=job_config).result()
    return result


# TODO(pnasrat): wire in prometheus values
def get_shared_hub_costs(cluster, start_month, end_month):
    totals = get_dedicated_cluster_costs(cluster, start_month, end_month)
    return totals


def get_from_prom():
    url, s = get_cluster_prometheus("2i2c")
    rows = defaultdict(list)
    query = """sum(
      kube_pod_container_resource_requests{resource="memory",unit="byte"}
    ) by (namespace)
    """
    resp = s.get(
        f"{url}/api/v1/query_range",
        params={
            "query": query,
            "start": "2023-03-01T00:00:00Z",
            "end": "2023-03-03T00:00:00Z",
            "step": "24h",
        },
    )
    if resp.status_code != 200:
        return []
    results = resp.json()["data"]["result"]
    for result in results:
        metric, values = result["metric"], result["values"]
        namespace = metric.get("namespace")
        for timestamp, memory in values:
            timestamp = datetime.fromtimestamp(timestamp)
            rows[timestamp].append((namespace, memory))
    return rows


def get_support_hub_costs(cluster, start_month, end_month):
    return []


def get_uptime_check_costs(project, start_month, end_month):
    return []
