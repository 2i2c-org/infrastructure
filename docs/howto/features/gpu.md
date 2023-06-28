(howto:features:gpu)=
# Enable access to GPUs

GPUs are heavily used in machine learning workflows, and we support
GPUs on all major cloud providers.

## Setting up GPU nodes

### GCP

#### Requesting quota increase

New GCP projects start with no GPU quota, so we must ask for some to enable
GPUs.

1. Go to the [GCP Quotas page](https://console.cloud.google.com/apis/api/compute.googleapis.com/quotas), 
   **and make sure you are in the right project**.
   
2. Search for "NVIDIA T4 GPU", and find the entry for the **correct region**.
   This is very important, as getting a quota increase in the wrong region means
   we have to do this all over again.

3. Check the box next to the correct quota, and click "Edit Quotas" button
   just above the list.

4. Enter the number of GPUs we want quota for on the right. For a brand new
   project, 4 is a good starting number. We can consistently ask for more,
   if these get used. GCP requires we provide a description for this quota
   increase request - "We need GPUs to work on some ML based research" is
   a good start. 
   
5. Click "Next", and then "Submit Request".

6. Sometimes the request is immediately granted, other times it takes a few
   days. 
   
#### Setting up GPU nodepools with terraform

The `notebook_nodes` variable for our GCP terraform accepts a `gpu`
parameter, which can be used to provision a GPU nodepool. An example
would look like:

```terraform
notebook_nodes = {
  "gpu-t4": {
    min: 0,
    max: 20,
    machine_type: "n1-highmem-8",
    gpu: {
      enabled: true,
      type: "nvidia-tesla-t4",
      count: 1
    },
    # Optional, in case we run into resource exhaustion in the main zone
    zones: [
      "us-central1-a",
      "us-central1-b",
      "us-central1-c",
      "us-central1-f"
    ]
  }
}
```

This provisions a `n1-highmem-8` node, where each node has 1 NVidia
T4 GPU.

In addition, we could ask for GPU nodes to be spawned in whatever zone
available in the same region, rather than just the same zone as the rest
of our notebook nodes. This should only be used if we run into GPU scarcity
issues in the zone!

### AWS

#### Requesting Quota Increase

On AWS, GPUs are provisioned by using P series nodes. Before they
can be accessed, you need to ask AWS for increased quota of P
series nodes.

1. Login to the AWS management console of the account the cluster is
   in.
2. Make sure you are in same region the cluster is in, by checking the
   region selector on the top right. **This is very important**, as getting
   a quota increase in the wrong region means we have to do this all over
   again.
3. Open the [EC2 Service Quotas](https://us-west-2.console.aws.amazon.com/servicequotas/home/services/ec2/quotas)
   page
4. Select 'Running On-Demand G and VT Instances' quota - this provisions NVidia T4
   GPUs (which are the `G4dn` instance type).
5. Select 'Request Quota Increase'.
6. Input the *number of vCPUs* needed. This translates to a total
   number of GPU nodes based on how many CPUs the nodes we want have.
   For example, if we are using [G4 nodes](https://aws.amazon.com/ec2/instance-types/g4/)
   with NVIDIA T4 GPUs, each `g4dn.xlarge` node gives us 1 GPU and
   4 vCPUs, so a quota of 8 vCPUs will allow us to spawn 2 GPU nodes.
   We should fine tune this calculation for later, but for now, the
   recommendation is to give users a single `g4dn.xlarge` each, so the number
   of vCPUs requested should be `4 * max number of GPU nodes`.
7. Ask for the increase, and wait. This can take *several working days*,
   so do it as early as possible!

#### Setup GPU nodegroup on eksctl

We use `eksctl` with `jsonnet` to provision our kubernetes clusters on
AWS, and we can configure a node group there to provide us GPUs.

1. In the `notebookNodes` definition in the appropriate `.jsonnet` file,
   add a node definition for the appropriate GPU node type:

   ```
    {
        instanceType: "g4dn.xlarge",
        tags+: {
            "k8s.io/cluster-autoscaler/node-template/resources/nvidia.com/gpu": "1"
        },
    }
   ```

   `g4dn.xlarge` gives us 1 Nvidia T4 GPU and ~4 CPUs. The `tags` definition
   is necessary to let the autoscaler know that this nodegroup has
   1 GPU per node. If you're using a different machine type with
   more GPUs, adjust this definition accordingly.

2. Render the `.jsonnet` file into a `.yaml` file that `eksctl` can use

   ```bash
   export CLUSTER_NAME=<your_cluster>
   ```

   ```bash
   jsonnet $CLUSTER_NAME.jsonnet > $CLUSTER_NAME.eksctl.yaml
   ```

3. Create the nodegroup

   ```bash
   eksctl create nodegroup -f $CLUSTER_NAME.eksctl.yaml
   ```

   This should create the nodegroup with 0 nodes in it, and the
   autoscaler should recognize this! `eksctl` will also setup the
   appropriate driver installer, so you won't have to.

## Setting up a GPU user profile

Finally, we need to give users the option of using the GPU via
a profile. This should be placed in the hub configuration:

```yaml
jupyterhub:
   singleuser:
      profileList:
        - display_name: NVIDIA Tesla T4, ~16 GB, ~4 CPUs
          description: "Start a container on a dedicated node with a GPU"
          profile_options:
            image:
              display_name: Image
              choices:
                tensorflow:
                  display_name: Pangeo Tensorflow ML Notebook
                  slug: "tensorflow"
                  kubespawner_override:
                    image: "pangeo/ml-notebook:<tag>"
                pytorch:
                  display_name: Pangeo PyTorch ML Notebook
                  default: true
                  slug: "pytorch"
                  kubespawner_override:
                    image: "pangeo/pytorch-notebook:<tag>"
          kubespawner_override:
            environment:
              NVIDIA_DRIVER_CAPABILITIES: compute,utility
            mem_limit: null
            mem_guarantee: 14G
            node_selector:
              node.kubernetes.io/instance-type: g4dn.xlarge
            extra_resource_limits:
              nvidia.com/gpu: "1"
```

1. If using a `daskhub`, place this under the `basehub` key.
2. The image used should have ML tools (pytorch, cuda, etc)
   installed. The recommendation is to provide Pangeo's
   [ml-notebook](https://hub.docker.com/r/pangeo/ml-notebook)
   for tensorflow and [pytorch-notebook](https://hub.docker.com/r/pangeo/pytorch-notebook)
   for pytorch. We expose these as options so users can pick what they want
   to use.

   ```{warning}
   **Do not** use the `latest` or `master` tags - find
   a specific tag listed for the image you want, and use that.
   ```

3. The [`NVIDIA_DRIVER_CAPABILITIES`](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/user-guide.html#driver-capabilities)
   environment variable tells the GPU driver what kind of libraries
   and tools to inject into the container. Without setting this,
   GPUs can not be accessed.
4. The `node_selector` makes sure that these user pods end up on
   the appropriate nodegroup we created earlier. Change the selector
   and the `mem_guarantee` if you are using a different kind of node

Do a deployment with this config, and then we can test to make sure
this works!

## Testing

1. Login to the hub, and start a server with the GPU profile you
   just set up.
2. Open a terminal, and try running `nvidia-smi`. This should provide
   you output indicating that a GPU is present.
3. Open a notebook, and run the following python code to see if
   tensorflow can access the GPUs:

   ```python
   import tensorflow as tf
   tf.config.list_physical_devices('GPU')
   ```

   This should output something like:

   ```
   [PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU')]
   ```

   If on an image with pytorch instead, try this:

   ```python
   import torch

   torch.cuda.is_available()
   ```

   This should return `True`.
4. Remember to explicitly shut down your server after testing,
   as GPU instances can get expensive!

If either of those tests fail, something is wrong and off you go debugging :)
