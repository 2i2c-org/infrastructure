# Tools used in this repo

## Base tools

These are helpful for everyone, and not cloud-specific.

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

### [`Helm`](https://helm.sh/)

Helm is used in two ways:

1. By our deployment scripts to deploy our hubs.
2. To deploy cluster-wide support components (such as prometheus, grafana,
   nginx-ingress) for each cluster.


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

## Google Cloud tools

[`google-cloud-sdk`](https://cloud.google.com/sdk/docs/install) is the primary
commandline tool used to interact with Google Cloud Platform (GCP). Our deployment
scripts use it to authenticate to GCP, and it is very helpful in [debugging node
issues](../howto/operate/node-administration.md).