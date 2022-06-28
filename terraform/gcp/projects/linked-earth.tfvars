prefix           = "linked-earth"
project_id       = "linked-earth-hubs"
zone             = "us-central1-c"
region           = "us-central1"

notebook_nodes = {
  "user" : {
    min : 0,
    max : 20,
    machine_type : "n1-highmem-4",
    labels: { },
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  }
}

dask_nodes = {
  "worker" : {
    min : 0,
    max : 100,
    machine_type : "n1-highmem-4",
    labels: { },
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  }
}

hub_cloud_permissions = {
  "staging" : {
    requestor_pays : false,
    bucket_admin_access: [],
    hub_namespace: "staging"
  }
}

container_repos = [ ]
