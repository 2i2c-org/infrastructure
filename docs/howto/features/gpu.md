(howto:features:gpu=)
# Enable access to GPUs

GPUs are heavily used in machine learning workflows, and we support
GPUs on all major cloud providers.

## Setting up GPU nodes

### AWS

#### Requesting Quota Increase

On AWS, GPUs are provisioned by using P series nodes. Before they
can be accessed, you need to ask AWS for increased quota of P
series nodes.

1. Login to the AWS management console of the account the cluster i
   in.
2. Make sure you are in same region the cluster is in, by checking the
   region selector on the top right.
3. Open the [EC2 Service Quotas](https://us-west-2.console.aws.amazon.com/servicequotas/home/services/ec2/quotas)
   page
4. Select 'Running On-Demand P Instances' quota
5. Select 'Request Quota Increase'.
6. Input the *number of vCPUs* needed. This translates to a total
   number of GPU nodes based on how many CPUs the nodes we want have.
   For example, if we are using [P2 nodes](https://aws.amazon.com/ec2/instance-types/p2/)
   with NVIDIA K80 GPUs, each `p2.xlarge` node gives us 1 GPU and
   4 vCPUs, so a quota of 8 vCPUs will allow us to spawn 2 GPU nodes.
   We should fine tune this calculation for later, but for now, the
   recommendation is to give users a `p2.xlarge` each, so the number
   of vCPUs requested should be `4 * max number of GPU nodes`.
7. Ask for the increase, and wait. This can take *several working days*.

#### Setup GPU nodegroup on eksctl

We use `eksctl` with `jsonnet` to provision our kubernetes clusters on
AWS, and we can configure a node group there to provide us GPUs.

1. In the `notebookNodes` definition in the appropriate `.jsonnet` file,
   add a node definition for the appropriate GPU node type:


   ```
    {
        instanceType: "p2.xlarge",
        tags+: {
            "k8s.io/cluster-autoscaler/node-template/resources/nvidia.com/gpu": "1"
        },
    }
   ```

   `p2.xlarge` gives us 1 K80 GPU and ~4 CPUs. The `tags` definition
   is necessary to let the autoscaler know that this nodegroup has
   1 GPU per node. If you're using a different machine type with
   more GPUs, adjust this definition accordingly.

2. Render the `.jsonnet` file into a `.yaml` file that `eksctl` can use

   ```bash
   jsonnet <your-cluster>.jsonnet > <your-cluster>.eksctl.yaml
   ```

3. Create the nodegroup

   ```bash
   eksctl create nodegroup -f <your-cluster>.eksctl.yaml --install-nvidia-plugin=false
   ```

   The `--install-nvidia-plugin=false` is required until
   [this bug](https://github.com/weaveworks/eksctl/issues/5277)
   is fixed.

   This should create the nodegroup with 0 nodes in it, and the
   autoscaler should recognize this!

#### Setting up a GPU user profile

Finally, we need to give users the option of using the GPU via
a profile. This should be placed in the hub configuration:

```yaml
jupyterhub:
    singleuser:
        profileList:
        - display_name: "Large + GPU: p2.xlarge"
          description: "~4CPUs, 60G RAM, 1 NVIDIA K80 GPU"
          kubespawner_override:
            mem_limit: null
            mem_guarantee: 55G
            image: "pangeo/ml-notebook:<tag>"
            environment:
              NVIDIA_DRIVER_CAPABILITIES: compute,utility
            extra_resource_limits:
              nvidia.com/gpu: "1"
            node_selector:
              node.kubernetes.io/instance-type: p2.xlarge
```

1. If using a `daskhub`, place this under the `basehub` key.
2. The image used should have ML tools (pytorch, cuda, etc)
   installed. The recommendation is to use Pangeo's
   [ml-notebook](https://hub.docker.com/r/pangeo/ml-notebook)
   for tensorflow and [pytorch-notebook](https://hub.docker.com/r/pangeo/pytorch-notebook)
   for pytorch. **Do not** use the `latest` or `master` tags - find
   a specific tag listed for the image you want, and use that.
3. The [NVIDIA_DRIVER_CAPABILITIES](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/user-guide.html#driver-capabilities)
   environment variable tells the GPU driver what kind of libraries
   and tools to inject into the container. Without setting this,
   GPUs can not be accessed.
4. The `node_selector` makes sure that these user pods end up on
   the appropriate nodegroup we created earlier. Change the selector
   and the `mem_guarantee` if you are using a different kind of node

Do a deployment with this config, and then we can test to make sure
this works!

#### Testing

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
4. Remember to explicitly shut down your server after testing,
   as GPU instances can get expensive!

If either of those tests fail, something is wrong and off you go debugging :)