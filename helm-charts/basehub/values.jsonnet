local hub_name = std.extVar('VARS_2I2C_HUB_NAME');

// Assume we are a staging hub if the word 'staging' is in the
// name of the hub.
local is_staging = std.member(hub_name, 'staging');

local emitDaskHubCompatibleConfig(basehubConfig) =
  // Handle legacy 'daskhub' type hubs
  // Note: This relies on `jsonnet` being called with absolute path to
  // the file, and the symlink from helm-charts/daskhub/values.jsonnet
  local isDaskHub = std.splitLimitR(std.thisFile, '/', 3)[2] == 'daskhub';

  if isDaskHub then { basehub: basehubConfig } else basehubConfig;

local nonStagingResourcesConfig = {
  'jupyterhub-home-nfs'+: {
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
  },
  jupyterhub+: {
    scheduling+: {
      userScheduler+: {
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
    },
    proxy+: {
      chp+: {
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
    },
    hub+: {
      resources+: {
        requests: {
          cpu: 0.01,
          memory: '128Mi',
        },
        limits: {
          memory: '2Gi',
        },
      },
    },
  },
  'jupyterhub-groups-exporter'+: {
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
  },
  nfs+: {
    dirsizeReporter+: {
      # Provide limited resources for this collector, as it can
      # balloon up (especially in CPU) quite easily. We are quite ok with
      # the collection taking a while as long as we aren't costing too much
      # CPU or RAM
      resources+: {
        requests: {
          memory: '128Mi',
          cpu: 0.01,
        },
        limits: {
          cpu: 0.05,
          memory: '512Mi'
        }
      }
    }
  }
};

local jupyterhubHomeNFSConfig = {
  'jupyterhub-home-nfs'+: {
    quotaEnforcer+: {
      config: {
        QuotaManager: {
          paths: ['/export/%s' % hub_name],
          hard_quota: 0,
        },
      },
    },
  },
};


emitDaskHubCompatibleConfig({
  'jupyterhub-home-nfs': jupyterhubHomeNFSConfig,
} + if is_staging then {} else nonStagingResourcesConfig)
