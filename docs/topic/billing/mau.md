# Monthly Active Users (MAU)

## Definition

We define an active user as someone who has:

1. Started a server, for any duration of time
2. Is not our health check service account `deployment-service-check`
3. Is not a 2i2c employee (for GitHub & Google IDs)

## Generating MAU metrics

You can generate MAU metrics for all clusters by running `deployer generate mau YYYY-MM`. You can generate a csv file with the output by passing a filename to the `--csv-file` parameter.
