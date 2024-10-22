# About code files

The code is meant to help serve grafana with JSON with cost related data from
AWS Cost Explorer API. It doesn't doesn't rely to other k8s services, so it can
deploy and be tested by itself.

The code files in this folders are mounted instead of built into the image in
order to quicken up development iterations running the code in k8s becomes
faster.

## Development

### Testing Python changes locally

First authenticate yourself against an AWS account.

```bash
cd helm-charts/aws-ce-grafana-backend/mounted-files
export AWS_CE_GRAFANA_BACKEND__CLUSTER_NAME=<name of cluster according to eksctl config>
python -m flask --app=webserver run --port=8080

# visit http://localhost:8080/hub-names
```

### Testing Python changes in k8s

This requires a k8s ServiceAccount coupled to an IAM Role prepared in advance
via terraform.

The image shouldn't need to be rebuilt unless additional dependencies needs to
be installed etc, so if you've only made code changes, you can do the following
to re-deploy.

During development, a procedure like below can be used to iterate faster than by
using the deployer.

```bash
deployer use-cluster-credentials $CLUSTER_NAME

cd helm-charts/aws-ce-grafana-backend
helm upgrade --install --create-namespace -n support --values my-test-config.yaml aws-ce-grafana-backend .

# note that port-forward to a service is just a way to port-forward to a pod
# behind the service, so you need to do the port-forwarding again if the pod
# restarts.
kubectl port-forward -n support service/aws-ce-grafana-backend 8080:http

# visit http://localhost:8080/hub-names and other urls
```

It assumes that you have a `my-test-config.yaml` file looking like this:

```yaml
serviceAccount:
  annotations:
    # can be setup via terraform by setting the variable
    # enable_aws_ce_grafana_backend_iam = true
    #
    # note that the terraform managed IAM Role's assume policy is
    # only granting a k8s ServiceAccount in "support" namespace
    # named "aws-ce-grafana-backend" rights to assume it
    #
    eks.amazonaws.com/role-arn: arn:aws:iam::783616723547:role/aws_ce_grafana_backend_iam_role
envBasedConfig:
  # note that this must be the AWS EKS cluster resource name,
  # not what we call the cluster
  clusterName: openscapeshub
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
