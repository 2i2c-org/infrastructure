local hub_name = std.extVar('VARS_2I2C_HUB_NAME');
local provider = std.extVar('VARS_2I2C_PROVIDER');

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

local nfsConfig = {
  dirsizeReporter: {
    reportTotalSize: provider == 'kubeconfig',
  },
  volumeReporter: {
    enabled: provider == 'kubeconfig',
  },
};

emitDaskHubCompatibleConfig({
  nfs: nfsConfig,
  'jupyterhub-home-nfs': jupyterhubHomeNFSConfig,
  'jupyterhub-groups-exporter': jupyterhubGroupsExporterConfig,
})
