# Tools used in this repo

## Base tools

These are helpful for everyone, and not cloud provider-specific.

### [`kubectl`](https://kubernetes.io/docs/tasks/tools/)

The canonical commandline tool for talking to kubernetes clusters.
Debugging and understanding runtime behavior of our hubs is greatly
enhanced by knowledge of how to use `kubectl`. Understanding how to
use `kubectl` really helps understand how kubernetes itself works.

#### Tips

- Consider aliasing it to `k`, as you might be typing it a lot!
- It is easy to accidentally operate on the wrong kubernetes cluster!
  Putting the current kubernetes context in your terminal prompt
  (via something like [starship](https://starship.rs/)) can help a
  lot!

#### Additional resources and tools

- The [official cheatsheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/),
  with extremely helpful tips.
- [Lens](https://k8slens.dev/) is an amazing GUI for exploring various objects
  in a kubernetes cluster. It can do almost everything `kubectl` does, in
  a fairly intuitive way. Highly recommended as a supplement (or even alternative)
  to `kubectl`.
- [k9s](https://k9scli.io/) is a similar tool to Lens, but a terminal based UI.
- Check out the [list of kubectl plugins](https://github.com/ishantanu/awesome-kubectl-plugins)
  to see if anything will help with your workflow.
- [`kubectx`](https://github.com/ahmetb/kubectx) helps with switching
  between different k8s clusters and namespaces, which we might have to do
  often.

(tools:helm)=
### [`Helm`](https://helm.sh/)

Helm is used in two ways:

1. By our deployment scripts to deploy our hubs.
2. To deploy cluster-wide support components (such as prometheus, grafana,
   nginx-ingress) for each cluster.

#### Tips

- The `--repo` flag allow you to specify a Helm repo directly instead of needing
  to do `helm repo add` and `helm repo update` first.
  ```bash
  helm template --repo https://jupyterhub.github.io/helm-chart/ jupyterhub
  ```
- The `helm template` command can quickly render templates for you which is a
  big part of developing a helm chart.
- The `helm template --show-only` flag can help you review a specific template.
  ```bash
  # 1. An example on how to access a specific template
  helm template --repo https://jupyterhub.github.io/helm-chart/ jupyterhub \
      --show-only templates/hub/deployment.yaml

  # 2. An example on how to access a specific template from a subchart
  #
  #    Note we need to specify version as the helm repo doesn't contain a valid
  #    binderhub version that isn't considered a pre-release.
  helm template --repo https://jupyterhub.github.io/helm-chart/ binderhub \
      --version=0.2.0-n611.he777436 \
      --set jupyterhub.hub.services.binder.apiToken=asd \
      --show-only charts/jupyterhub/templates/hub/deployment.yaml
  ```
- The `helm template --validate` flag can help you both render and then validate
  the rendered templates with a k8s api-server. This is an excellent lightweight
  test of a Helm chart in a CI system.

(tools:sops)=
### [`sops`](https://github.com/mozilla/sops/)

In line with 2i2c's [Customer Right to Replicate](https://2i2c.org/right-to-replicate/),
we try to keep all our deployment repositories as open as possible. But
some values *must* be secret - like access tokens, cookie secret seeds, etc.
We use `sops` to store them encrypted in our Git repo, so they can be version
controlled and reviewed along with the rest of the repo. We use
[Google Cloud KMS](https://github.com/mozilla/sops/#23encrypting-using-gcp-kms)
to encrypt our secrets, so you need the Google Cloud tools installed and
authenticated locally (following [the instructions here](https://github.com/mozilla/sops/#23encrypting-using-gcp-kms))
before you can use sops.

`sops` is called programatically by our deployment scripts to decrypt
files for deployment, and you will use it interactively to modify or encrypt
new files.

(tools:terraform)=
### Terraform


[Terraform](https://www.terraform.io/) is an "Infrastructure as Code" (IaC) tool that allows you to build, change, and version infrastructure in the cloud.
We use terraform to provision cloud infrastructure and modify it directly.
We then deploy applications on top of that infrastructure via [Helm](tools:helm).

The minimum required version is `1.3`.

## Google Cloud tools

[`google-cloud-sdk`](https://cloud.google.com/sdk/docs/install) is the primary
commandline tool used to interact with Google Cloud Platform (GCP). Our deployment
scripts use it to authenticate to GCP, and it is very helpful in [debugging node
issues](../sre-guide/manage-k8s/node-administration.md).

### Tips

(tools:gcloud:auth)=
#### Authentication

`gcloud` has two authentication flows, and that can get quite confusing since we
work on a number of clusters with different Google credentials.

[`gcloud auth login`](https://cloud.google.com/sdk/gcloud/reference/auth/login)
provides credentials for `gcloud` commands like `gcloud compute instances list`
or `gcloud container clusters list`.

[`gcloud auth application-default login`](https://cloud.google.com/sdk/gcloud/reference/auth/application-default/login)
provides credentials for *other tools* (such as `helm`, `kubectl`, `sops`) to
authenticate to Google Cloud Platform on your behalf. So if `sops` or
`kubectl` is complaining about authentication, make sure you are authenticated
correctly with `application-default`

## AWS tools

### awscli

The [AWS Command Line Interface (CLI)](https://docs.aws.amazon.com/cli/index.html) is a
unified tool to manage your AWS services.
With just one tool to download and configure, you can control multiple AWS services from the command line and automate them through scripts.

### eksctl

`eksctl` is a simple CLI tool for creating and managing clusters on EKS - Amazon's
managed Kubernetes service for EC2. See [the `eksctl` documentation for more information](https://docs.aws.amazon.com/eks/latest/userguide/getting-started-eksctl.html).

Make sure you are using at least version 0.115. You
can check the installed version with `eksctl version`
