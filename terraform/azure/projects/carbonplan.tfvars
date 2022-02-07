tenant_id          = "d6b0296c-4d43-4983-93b0-36248aa9c592"
subscription_id    = "c5e7a734-3dbf-4285-80e5-4c0afb1f65dc"
resourcegroup_name = "2i2c-carbonplan-cluster"
location           = "westeurope"

ssh_pub_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCrtD6l/2S2dDT1OFLIUa46KAuzlUkckneQ4oyK5c2izT0nlBOxOcWACvnJ4rqntZVuhML7GYS35tQQnXyEXctTS2LnB7illl+oCT63WQzhhutfPLZSW3gJ+/CFVVp0VdHq4t1O8CQO+EgeV1cvuBre/neNZo5tcqXEsoV7tw/qw8XmD7Dk3yPz4NEFYZyZ4xQM7Qn2j9krZlRO2wCrosMFLo5Rv108PSDTHn3VtXEpJwemUO93D0ipJvCDE62M3vJxamqP4k5HLVn3Jun5KEvA7fINvgP3NSXkPVEEE4Prcqc1IJIzSxzygEN7xkZYsUEfJkybGXUWtUXdNjOEfLLlhYToMhdcP4jZluAjTtQmnJTr1sLegH+kbGIvI8MFIJAgXXLXS8/ubXHMozb+4gXRhyT8SMPwmgXGA+FtDduy5gnpPMSgmozQY17av5r25T6viWX5ivtL+n/CNJGf4npM1vKWcUNKiGyJrwzxQdpwJZ2uMP3EIdCYxOvqCQ+7UEM= sgibson@Athena.broadband"

global_container_registry_name = "2i2ccarbonplanhubregistry"
global_storage_account_name    = "2i2ccarbonplanhubstorage"
storage_protocol               = "NFS"

notebook_nodes = {
  "small" : {
    min : 0,
    max : 20,
    vm_size : "Standard_E2s_v4",
    labels: { },
    taints: [ ],
    kubernetes_version = "",
  },
  "medium" : {
    min : 0,
    max : 20,
    vm_size : "Standard_E4s_v4",
    labels: { },
    taints: [ ],
    kubernetes_version = "",
  },
  "large" : {
    min : 0,
    max : 20,
    vm_size : "Standard_E8s_v4",
    labels: { },
    taints: [ ],
    kubernetes_version = "",
  },
  "huge" : {
    min : 0,
    max : 20,
    vm_size : "Standard_E32s_v4",
    labels: { },
    taints: [ ],
    kubernetes_version = "",
  },
  "vhuge" : {
    min : 0,
    max : 20,
    vm_size : "Standard_M64s_v2",
    labels: { },
    taints: [ ],
    kubernetes_version = "",
  },
  "vvhuge" : {
    min : 0,
    max : 20,
    vm_size : "Standard_M128s_v2",
    labels: { },
    taints: [ ],
    kubernetes_version = "",
  },
    "gpu" : {
    min : 0,
    max : 20,
    vm_size : "Standard_NC24s_v3",
    labels: {
      "hub.jupyter.org/sku": "gpu",
    },
    taints: [ ],
    kubernetes_version = "1.19.13",
  },
}

dask_nodes = {
  "small" : {
    min : 0,
    max : 20,
    vm_size : "Standard_E2s_v4",
    labels: { },
    taints: [ ],
    kubernetes_version = "",
  },
  "medium" : {
    min : 0,
    max : 20,
    vm_size : "Standard_E4s_v4",
    labels: { },
    taints: [ ],
    kubernetes_version = "",
  },
  "large" : {
    min : 0,
    max : 20,
    vm_size : "Standard_E8s_v4",
    labels: { },
    taints: [ ],
    kubernetes_version = "",
  },
  "huge" : {
    min : 0,
    max : 20,
    vm_size : "Standard_E32s_v4",
    labels: { },
    taints: [ ],
    kubernetes_version = "",
  },
  "vhuge" : {
    min : 0,
    max : 20,
    vm_size : "Standard_M64s_v2",
    labels: { },
    taints: [ ],
    kubernetes_version = "",
  },
  "vvhuge" : {
    min : 0,
    max : 20,
    vm_size : "Standard_M128s_v2",
    labels: { },
    taints: [ ],
    kubernetes_version = "",
  },
  "gpu" : {
    min : 0,
    max : 20,
    vm_size : "Standard_NC24s_v3",
    labels: {
      "hub.jupyter.org/sku": "gpu",
    },
    taints: [ ],
    kubernetes_version = "1.19.13",
  },
}
