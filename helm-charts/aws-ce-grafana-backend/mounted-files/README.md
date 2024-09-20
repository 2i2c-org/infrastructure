# About code files

The code is meant to help serve grafana with JSON with cost related data,
initially only from AWS.

## De-coupled from other k8s services

This software doesn't rely to other k8s services, so it can deploy and be tested
by itself.

## Bundling into Dockerfile vs. mounting in Helm chart

By mounting the code files, development iterations running the code in k8s
becomes faster.

## Development

### Testing Python changes locally

First authenticate yourself against the AWS openscapes account.

```bash
cd helm-charts/aws-ce-grafana-backend/mounted-files
export AWS_CE_GRAFANA_BACKEND__CLUSTER_NAME=openscapeshub
python -m flask --app=webserver run --port=8080

# visit http://localhost:8080/aws
```

### Testing Python changes in k8s

This is currently being developed in the openscapes cluster. It depends on a k8s
ServiceAccount coupled to an IAM Role there as well.

The image shouldn't need to be rebuilt unless additional dependencies needs to
be installed etc, so if you've only made code changes, you can do the following
to re-deploy.

```bash
deployer use-cluster-credentials openscapes

cd helm-charts/aws-ce-grafana-backend
helm upgrade --install --create-namespace -n ce-test --values ce-test-config.yaml ce-test .

# note that port-forward to a service is just a way to port-forward to a pod
# behind the service, so you need to do the port-forwarding again if the pod
# restarts.
kubectl port-forward -n ce-test service/ce-test 8080:http

# visit http://localhost:8080/aws
```

### Testing image changes in k8s

```bash

cd helm-charts

# before doing this: commit the image change, and stash other changes
#                    git status should not report anything
chartpress --push

# commit the updated image tag
git add aws-ce-grafana-backend/values.yaml
git commit -m "aws-ce-grafana-backend chart: update image to deploy"

# WARNING: cleanup of uncommitted files, should be ok if your git status was
#          clean before running chartpress --push
git reset --hard HEAD
```
