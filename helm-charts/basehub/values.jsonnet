local hub_name = std.extVar('VARS_2I2C_HUB_NAME');
local cluster_name = std.extVar('VARS_2I2C_CLUSTER_NAME');
local provider = std.extVar('VARS_2I2C_PROVIDER');
local hub_domain = std.extVar('VARS_2I2C_HUB_DOMAIN');
local account_id = std.extVar('VARS_2I2C_ACCOUNT_ID');

// Assume we are a staging hub if the word 'staging' is in the
// name of the hub.
local is_staging = std.member(hub_name, 'staging');

local emitDaskHubCompatibleConfig(basehubConfig) =
  // Handle legacy 'daskhub' type hubs
  // Note: This relies on `jsonnet` being called with absolute path to
  // the file, and the symlink from helm-charts/daskhub/values.jsonnet
  local isDaskHub = std.splitLimitR(std.thisFile, '/', 3)[2] == 'daskhub';

  if isDaskHub then { basehub: basehubConfig } else basehubConfig;

local jupyterhubHomeNFSResources = {
  quotaEnforcer+: {
    resources: {
      requests: {
        cpu: 0.2,
        memory: '750M',
      },
      limits: {
        cpu: 0.4,
        memory: '1G',
      },
    },
  },
  nfsServer+: {
    resources: {
      requests: {
        cpu: 0.2,
        memory: '2G',
      },
      limits: {
        cpu: 0.4,
        memory: '6G',
      },
    },
  },
  prometheusExporter+: {
    resources: {
      requests: {
        cpu: 0.02,
        memory: '15M',
      },
      limits: {
        cpu: 0.04,
        memory: '20M',
      },
    },
  },
  autoResizer+: {
    resources: {
      requests: {
        cpu: 0.01,
        memory: '64Mi',
      },
      limits: {
        memory: '1Gi',
      },
    },
  },
};

local jupyterhubHomeNFSConfig = {
  eks: {
    enabled: provider == 'aws',
  },
  gke: {
    enabled: provider == 'gcp',
  },
  quotaEnforcer+: {
    config: {
      QuotaManager: {
        paths: ['/export/%s' % hub_name],
        hard_quota: if is_staging then 1 else 10,
        projects_file: '/export/%s/.projects' % hub_name,
        projid_file: '/export/%s/.projid' % hub_name,
        log_level: 'INFO',
      },
    },
  },
} + if is_staging then {} else jupyterhubHomeNFSResources;

local jupyterhubGroupsExporterConfig = {
  // Config values
  config: {
    groupsExporter: {
      update_info_interval: 3600,
      update_metrics_interval: 300,
      update_dirsize_interval: 3600,
      prometheus_host: 'support-prometheus-server.support.svc.cluster.local',
      prometheus_port: 80,
    },
  },
  // Memory resources chosen by querying PromQL "max(container_memory_working_set_bytes{name!='', pod=~'.*groups-exporter.*'})" over all hubs
  // CPU resources chosen by querying PromQL "max(irate(container_cpu_usage_seconds_total{name!='', pod=~'.*groups-exporter.*'}[5m]))" over all hubs
  resources: {
    requests: {
      cpu: 0.01,
      memory: '128Mi',
    },
    limits: {
      cpu: 0.1,
      memory: '256Mi',
    },
  },
};

local pvConfig =
  if provider == 'gcp' then {
    pv: {
      serverIP: 'storage-quota-home-nfs.%s.svc.cluster.local' % hub_name,
      // We pick soft over hard, so NFS lockups don't lead to hung processes
      mountOptions: ['soft', 'noatime'],
    },
  } else
    if provider == 'aws' then {
      pv: {
        mountOptions: [
          'rsize=1048576',
          'wsize=1048576',
          'timeo=600',
          'soft',
          'retrans=2',
          'noresvport',
        ],
      },
    } else {};

local nfsConfig = {
  dirsizeReporter: {
    reportTotalSize: provider == 'kubeconfig',
  },
  volumeReporter: {
    enabled: provider == 'kubeconfig',
  },
} + pvConfig;

local hubIngressConfig = {
  hosts: [hub_domain],
  tls: [
    {
      hosts: [hub_domain],
      secretName: 'https-auto-tls',
    },
  ],
};

local jupyterhubConfig = {
  ingress: hubIngressConfig,
  hub: {
    config: {
      OAuthenticator: {
        // Always set oauth callback URL, to prevent it from being
        // guessed 'wrong'.
        oauth_callback_url: 'https://%s/hub/oauth_callback' % [hub_domain],
      },
    },
  },
  singleuser: {
    nodeSelector: {
      '2i2c/hub-name': hub_name,
    },
  },
};

local daskGatewayConfig = {
  gateway: {
    backend: {
      scheduler: {
        extraPodConfig: {
          nodeSelector: {
            '2i2c/hub-name': hub_name,
          },
        },
      },
      worker: {
        extraPodConfig: {
          nodeSelector: {
            '2i2c/hub-name': hub_name,
          },
        },
      },
    },
  },
};

local binderhubServiceConfig = {
  // Schedule builder pods to run on the default smallest user nodes
  // https://github.com/2i2c-org/infrastructure/issues/4241
  dockerApi: {
    nodeSelector: {
                    '2i2c/hub-name': hub_name,
                  } +
                  if provider == 'aws' then {
                    'node.kubernetes.io/instance-type': 'r5.xlarge',
                  }
                  else if provider == 'gcp' then {
                    'node.kubernetes.io/instance-type': 'n2-highmem-4',
                  } else {},
  },
  config: {
    KubernetesBuildExecutor: {
      node_selector: {
                       '2i2c/hub-name': hub_name,
                     } +
                     if provider == 'aws' then {
                       'node.kubernetes.io/instance-type': 'r5.xlarge',
                     }
                     else if provider == 'gcp' then {
                       'node.kubernetes.io/instance-type': 'n2-highmem-4',
                     } else {},
    },
  },
};

// We define a service account that is attached by default to all Jupyter user pods
// and dask-gateway workers. By default, this has no permissions for clusters not
// on GCP or AWS - see docs/topic/features.md.
local userServiceAccountConfig =
  {
    enabled: true,
  } +
  if provider == 'aws' then {
    annotations: {
      'eks.amazonaws.com/role-arn': 'arn:aws:iam::%s:role/%s-%s' % [account_id, cluster_name, hub_name],
    },
  } else if provider == 'gcp' then {
    annotations: {
      'iam.gke.io/gcp-service-account': '%s-%s@%s.iam.gserviceaccount.com' % [cluster_name, hub_name, account_id],
    },
  } else {
    annotations: {},
  };


emitDaskHubCompatibleConfig(
  {
    nfs: nfsConfig,
    'jupyterhub-home-nfs': jupyterhubHomeNFSConfig,
    'jupyterhub-groups-exporter': jupyterhubGroupsExporterConfig,
    jupyterhub: jupyterhubConfig,
    userServiceAccount: userServiceAccountConfig,
    'dask-gateway': daskGatewayConfig,
    'binderhub-service': binderhubServiceConfig,
  }
)
