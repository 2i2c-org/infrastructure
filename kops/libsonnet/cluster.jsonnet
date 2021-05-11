// local cluster(name, configBase, zone, masterIgName, networkCIDR, subnets) = {
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