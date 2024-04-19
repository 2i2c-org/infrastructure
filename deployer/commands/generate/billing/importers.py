import re

import pandas as pd
from google.cloud import bigquery
from prometheus_pandas import query

from deployer.commands.grafana.utils import get_cluster_prometheus


def build_gcp_query(cluster: dict, service_id=None):
    """Generate query string for GCP Billing Export BigQuery.

    Args:
        cluster (dict): parsed cluster yaml.
        service_id (string, optional): Optional Google Service ID. Defaults to None.

    Returns:
        string: query string
    """
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
    # Ensure service ID is valid
    by_service = ""
    if service_id is not None:
        assert re.match(r"^[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}$", service_id, re.I)
        by_service = f'AND service.id = "{service_id}"'

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
                {by_service}
            GROUP BY 1, 2
            ORDER BY invoice.month ASC
            ;
            """
    return query


class BigqueryGCPBillingCostImporter:
    def __init__(self, cluster: dict, service_id=None):
        """Bigquery Cost Importer for GCP clusters

        Args:
            cluster (dict): parsed cluster.yaml.
            service_id (string, optional): Optional Google Service ID. Defaults to None.
        """
        self.cluster = cluster
        self.cluster_project_name = cluster["gcp"]["project"]
        self.client = bigquery.Client()
        self.query = build_gcp_query(cluster, service_id)

    def get_costs(self, start_month, end_month):
        """Gets costs for a time period.

        Args:
            start_month (datetime.datetime): Start date of query.
            end_month (datetime.datetime): End date of query.

        Returns:
            pandas.DataFrame: dataframe of costs.
        """
        df = self._run_query(start_month, end_month)
        df["month"] = pd.to_datetime(df["month"], format="%Y%m")
        df = df.set_index("month")
        return df

    def _run_query(self, start_month, end_month):
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "start_month", "STRING", start_month.strftime("%Y%m")
                ),
                bigquery.ScalarQueryParameter(
                    "end_month", "STRING", end_month.strftime("%Y%m")
                ),
                bigquery.ScalarQueryParameter(
                    "project", "STRING", self.cluster_project_name
                ),
            ]
        )
        result = self.client.query(self.query, job_config=job_config).result()
        return result.to_dataframe()


class PrometheusUtilizationImporter:
    def __init__(self, cluster: dict):
        """Prometheus Utilization Importer for shared GCP clusters

        Args:
            cluster (dict): parsed cluster.yaml
        """
        self.cluster = cluster

    def get_utilization(self, start_month, end_month):
        """Gets utilization for a time period from prometheus.

        Args:
            start_month (datetime.datetime): Start date of query.
            end_month (datetime.datetime): End date of query.

        Returns:
            pandas.DataFrame: dataframe of utilization.
        """
        df = self._run_query(start_month, end_month)
        return self.clean_query_dataframe(df)

    def _run_query(self, start_month, end_month):
        url, s = get_cluster_prometheus(self.cluster.get("name"))
        p = query.Prometheus(url, http=s)
        prom_query = """sum(
        kube_pod_container_resource_requests{resource="memory",unit="byte"}
        ) by (namespace)
        """
        start = start_month.timestamp()
        end = end_month.timestamp()
        step = "24h"
        rows = p.query_range(prom_query, start, end, step)
        return rows

    def clean_query_dataframe(self, df):
        df = self.clean_namespace_labels(df)
        df.index.names = ["month"]
        df.fillna(0, inplace=True)
        df = df.resample("MS", axis=0).sum()
        # Calculate utilization
        df = df.div(df.sum(axis=1), axis=0)
        # Combined support
        df = self.combine_support(df)
        df = self.combine_internal_costs(df)
        return df

    def clean_namespace_labels(self, df):
        # This only handles single prometheus namespace labels rather than any general prometheus query.
        # The regex should be for an RFC 1123 DNS_LABEL however we're only querying namespaces so strict
        # validation not as necessary
        # https://github.com/kubernetes/design-proposals-archive/blob/main/architecture/identifiers.md
        df = df.rename(
            columns=lambda c: re.sub(
                r".*=\"(?P<namespace>[a-zA-Z0-9-]+)\"}", r"\g<namespace>", c
            ),
        )
        return df

    def combine_support(self, df):
        df["support_combined"] = 0.0
        if "support" in df:
            df["support_combined"] = df["support_combined"] + df["support"]

        if "kube-system" in df:
            df["support_combined"] = df["support_combined"] + df["kube-system"]
        return df.drop(columns=["support", "kube-system"], errors="ignore")

    def combine_internal_costs(self, df):
        # FIXME: This list was manually created during the Q1 2023 billing consolidation work.
        # Ideally needs to be in a system that represents contract lifecycle and cost responsibility.
        internal = {
            "utexas-demo",
            "staging",
            "demo",
            "dask-staging",
            "configconnector-operator-system",
            "cnrm-system",
            "binder-staging",
        }
        df["2i2c_costs"] = 0.0
        for namespace in internal.intersection(df.columns):
            df["2i2c_costs"] += df[namespace]
        return df.drop(internal, axis=1, errors="ignore")


def get_cluster_costs(cluster, start_month, end_month):
    tenancy = cluster.get("tenancy", "dedicated")
    if tenancy == "shared":
        return get_shared_cluster_hub_costs(cluster, start_month, end_month)
    elif tenancy == "dedicated":
        return get_dedicated_cluster_costs(cluster, start_month, end_month)
    return pd.DataFrame()


def get_dedicated_cluster_costs(cluster, start_month, end_month):
    """Return monthly costs for a dedicated cluster.

    Args:
        cluster (dict): parsed cluster.yaml
        start_month (datetime): Starting month
        end_month (datetime): End month

    Returns:
        pandas.DataFrame of costs.
    """
    bq_importer = BigqueryGCPBillingCostImporter(cluster)
    result = bq_importer.get_costs(start_month, end_month)
    return result


def get_shared_cluster_utilization(cluster, start_month, end_month):
    """Return monthly utilization for hubs in a shared cluster.

    Args:
        cluster (dict): parsed cluster.yaml
        start_month (datetime): Starting month
        end_month (datetime): End month

    Returns:
        pandas.DataFrame of utilization.
    """
    prom_importer = PrometheusUtilizationImporter(cluster)
    utilization = prom_importer.get_utilization(start_month, end_month)
    utilization = utilization.melt(
        ignore_index=False, var_name="hub", value_name="utilization"
    )
    return utilization


def get_shared_cluster_hub_costs(cluster, start_month, end_month):
    """Calculate monthly hub costs in shared cluster.

    Args:
        cluster (dict): parsed cluster.yaml
        start_month (datetime): Starting month
        end_month (datetime): End month

    Returns:
        pandas.DataFrame of monthly costs.
    """
    costs = get_dedicated_cluster_costs(cluster, start_month, end_month)
    utilization = get_shared_cluster_utilization(cluster, start_month, end_month)
    # Create single dataframe
    totals = costs.merge(utilization, how="left", on="month")
    # Rename project to use hub names
    totals["project"] = totals["hub"]
    totals.drop("hub", axis=1)
    # Calculate cost from utilization
    # Needs to account for uptime checks and 2i2c paid for stuff
    totals["cost"] = totals["utilization"].multiply(
        totals["total_with_credits"].astype(float), axis=0
    )
    # Reshape to output schema
    totals = totals.drop(["total_with_credits", "utilization", "hub"], axis=1).rename(
        {"cost": "total_with_credits"}, axis=1
    )
    # uptime checks
    return totals
