local cluster = import "./libsonnet/cluster.jsonnet";

cluster.makeCluster(
    "oceanhackweek-es",
    "us-west-2",
    "us-west-2a",
    "1.32",
    ["staging", "prod"]
)