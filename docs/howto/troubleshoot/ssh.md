# SSH into nodes

Sometimes, you need to directly SSH into a kubernetes node to troubleshoot an
issue. This document describes how to do that on various cloud providers.

## Kubernetes ephemeral containers

Kubernetes offers a feature to use debug pods to get a [node shell session](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/#node-shell-session).

This should work across cloud providers.

```
kubectl debug node/mynode -it --image=ubuntu
```

This creates a debug pod in the default namespace and drops you into a root
shell with the node filesystem mounted on `/host`. When finished debugging
delete the create debugger pod.


## GCP

1. Make sure you are [authenticated with gcloud](tools:gcloud:auth)

2. Set the `project` we are operating on, so `gcloud` knows where to look:

   ```
   gcloud config set project <name-of-project>
   ```
   
   ```{note}
   You can find the name of the project under `gcp.project` in the `cluster.yaml`
   file for the cluster.
   ```
   
3. Find the name of the node you want to login to, usually via `kubectl get node`.
   You can also find out the node a specific pod is on by `kubectl get node -o wide`.
   
4. SSH into the node with `gcloud compute ssh <node-name>`. This will set you up with
   a user who has `sudo` permissions on the node, so you can poke around!
   
   
## AWS

1. Make sure you are logged in to the `aws` commandline tool, and authenticated as yourself
   to have access to AWS organization under which this cluster lives. You can validate that
   with `aws sts get-caller-identity` - the output should include your personal username,
   *not* that of the hub deployer!
   
2. You also need the AWS [Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)
   installed.
   
3. Get the *instance id* of the node. Unlike with GCP, on AWS the instance id is not the same
   as the node-name reported by `kubectl get node` or `kubectl get pod -o wide`. The instance
   name is on the kubernetes node object as a label with name `alpha.eksctl.io/instance-id`.
   You can get the entire object's definition with `kubectl get node <node-name> -o yaml`, and
   pick out the `alpha.eksctl.io/instance-id` from there. This is of the form `i-<some-string>`.
   
4. Get the *region* of the node. From the output you got in step 3, you can look at the label
   `topology.kubernetes.io/region` to get the region. For us, it's often `us-west-2` (as that is
   where a lot of scientific data is stored)
   
5. You can now ssh with:

   ```bash
   aws ssm start-session --target <instance-id> --region <region>
   ```
   
6. This will put you on the node with the `sh` shell, which is missing a lot of the features we
   expect from interactive shells today. You can get on bash with `bash -l`.
   
7. You will be a user with full `sudo` access, so you can troubleshoot to your heart's content.
