# Automatic deployment with CI/CD

Most of our infrastructure automatically deploys and updates hubs via GitHub Workflows.
You can find [our deployment GitHub Actions configuration here](https://github.com/2i2c-org/infrastructure/blob/master/.github/workflows/deploy-hubs.yaml).

Each cloud provider requires a few cloud-specific steps to set up automatic deployment.

More information about our general CI/CD machinery is available in the [corresponding
reference section](/reference/ci-cd.md).

## Running the CI/CD machinery on each cloud provider

The following sections cover how to deploy hubs on the cloud providers that we support.

```{toctree}
aws.md
```

```{note}
TODO: write specific documentation for google cloud and azure cloud providers
```

## Setting up repo2docker-action

```{toctree}
split-repo2docker.md
```
