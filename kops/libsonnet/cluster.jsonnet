// Exports a customizable kops Cluster object.
// https://kops.sigs.k8s.io/cluster_spec/ lists available properties.
//
// The default configuration sets up the following:
//
// 1. One etcd cluster each on the master node for events & api,
//    with minimal resource allocations
// 2. Calico for in-cluster networking https://kops.sigs.k8s.io/networking/calico/,
//    with the default settings. Explicitly decided against AWS-VPC cluster networking
//    due to pod density issues - see https://github.com/2i2c-org/pangeo-hubs/issues/28.
// 3. Nodes in only one subnet in one AZ. Ideally, the master would be multi-AZ but
//    the nodes would be single AZ. Multi AZ workers run into problems attaching PVs
//    from other AZs (for hub db PVC, for example), and incurs networking cost for no
//    clear benefit in our use case. An opinionated set of IP ranges is picked here,
//    and the subnet is created in _config.zone.
// 4. kops defaults for networking - a /16 network for the entire cluster,
//    with a /19 allocated to the one subnet currently in use. This allows for
//    ~8000 currently active pods.
// 5. Kubernetes API and SSH access allowed from everywhere.
// 6. IAM Permissions to pull from ECR.
// 7. Enables feature gates to allow hub services to run on master node as well.
// 8. Docker as the container runtime.
//
// Supports passing a hidden `_config` object that takes the following
// keys:
// 1. masterInstanceGroupName
//    Name of the InstanceGroup that is the master. The etcd clusters will be
//    put on this.
// 2. zone
//    Zone where the cluster is to be set up
{
    _config+:: {
        masterInstanceGroupName: "",
        zone: "",
    },
    apiVersion: "kops.k8s.io/v1alpha2",
    kind: "Cluster",
    metadata: {
        name: ""
    },
    spec: {
        clusterAutoscaler: {
            enabled: true
        },
        api: {
            loadBalancer: {
                class: "Classic",
                type: "Public"
            }
        },
        authorization: {
            rbac: {}
        },
        dns: {
            kubeDNS: {
                provider: "CoreDNS"
            }
        },
        channel: "stable",
        cloudProvider: "aws",
        configBase: "",
        containerRuntime: "docker",
        etcdClusters: [
            {
                cpuRequest: "200m",
                etcdMembers: [
                    {
                        instanceGroup: $._config.masterInstanceGroupName,
                        name: "a"
                    }
                ],
                memoryRequest: "100Mi",
                name: "main"
            },
            {
                cpuRequest: "100m",
                etcdMembers: [
                    {
                        instanceGroup: $._config.masterInstanceGroupName,
                        name: "a"
                    }
                ],
                memoryRequest: "100Mi",
                name: "events"
            }
        ],
        iam: {
            allowContainerRegistry: true,
            legacy: false
        },
        kubelet: {
            anonymousAuth: false,
            featureGates: {
                // These boolean values need to be strings
                // Without these, services can't target pods running on the master node.
                // We want our hub core services to run on the master node, so we need
                // to set these.
                LegacyNodeRoleBehavior: "false",
                ServiceNodeExclusion: "false"
            }
        },
        kubeControllerManager: {
            featureGates: {
                // These boolean values need to be strings
                LegacyNodeRoleBehavior: "false",
                ServiceNodeExclusion: "false"
            }
        },
        kubernetesApiAccess: [
            // Allow access to the master API from everywhere
            "0.0.0.0/0"
        ],
        kubernetesVersion: "1.19.7",
        masterPublicName: "api.%s" % $.metadata.name,
        networkCIDR: "172.20.0.0/16",
        networking: {
            calico: {
                majorVersion: "v3"
            }
        },
        nonMasqueradeCIDR: "100.64.0.0/10",
        sshAccess: [
            "0.0.0.0/0"
        ],
        subnets: [{
            cidr: "172.20.32.0/19",
            name: $._config.zone,
            type: "Public",
            zone: $._config.zone
        }],
        topology: {
            dns: {
                type: "Public"
            },
            masters: "public",
            nodes: "public"
        }
    }
}