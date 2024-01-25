(howto-troubleshoot:kubectl-logs)=
# Kubectl logging

This page describes how to look at various logs by using some deployer commands that wrap the most common kubectl commands or by using kubectl directly. 

## Look at logs via deployer sub-commands

There are some `deployer debug` sub-commands that wrap up the most relevant `kubectl logs` arguments that allow conveniently checking logs with only one command.

````{tip}
You can export the cluster's and hub's names as environmental variables to directly use the copy-pasted commands in the sections below.

```bash
export CLUSTER_NAME=2i2c; export HUB_NAME=staging
```
````

### Look at hub component logs

The JupyterHub component's logs can be fetched with the `deployer debug component-logs` command, ran for each hub component.

These commands are standalone and **don't require** running `deployer use-cluster-credentials` before.

```{tip}
1. The `--no-follow` flag

   You can pass `--no-follow` to each of the deployer commands below to provide just logs up to the current point in time and then stop.

2. The `--previous` flag

   If the pod has restarted due to an error, you can pass `--previous` to look at the logs of the pod prior to the last restart.
```

(howto-troubleshoot:hub-pod-logs)=
#### Hub pod logs
```bash
deployer debug component-logs $CLUSTER_NAME $HUB_NAME hub
```

#### Proxy pod logs
```bash
deployer debug component-logs $CLUSTER_NAME $HUB_NAME proxy
```

(howto-troubleshoot:kubectl-traefik-logs)=
#### Traefik pod logs
```bash
deployer debug component-logs $CLUSTER_NAME $HUB_NAME traefik
```

(howto-troubleshoot:kubectl-dask-gateway-logs)=
### Look at dask-gateway logs

Display the logs from the dask-gateway's most important component pods.

#### Dask-gateway-api pod logs
```bash
deployer debug component-logs $CLUSTER_NAME $HUB_NAME dask-gateway-api
```

#### Dask-gateway-controller pod logs
```bash
deployer debug component-logs $CLUSTER_NAME $HUB_NAME dask-gateway-controller
```

### Look at a specific user's logs

Display logs from the notebook pod of a given user with the following command:

```bash
deployer debug user-logs  $CLUSTER_NAME $HUB_NAME <username>
```

Note that you don't need the *escaped* username, with this command.

## Look at logs via kubectl

### Pre-requisites

Get the name of the cluster you want to debug and export its name as env vars. Then use the `deployer` to gain `kubectl` access into this specific cluster.

Example:

```bash
export CLUSTER_NAME=2i2c;
deployer use-cluster-credentials $CLUSTER_NAME
```

(howto-troubleshoot:kubectl-autoscaler-logs)=
### Kubernetes autoscaler logs

You can find scale up or scale down events by looking for decision events

```
kubectl describe -n kube-system configmap cluster-autoscaler-status
```

### Kubernetes node events and status

1. Running nodes and their status
    ```bash
    kubectl get nodes
    ```

2. Get a node's events from the past 1h
    ```bash
    kubectl get events --field-selector involvedObject.kind=Node --field-selector involvedObject.name=<some-node-name>
    ```

3. Describe a node and any related events
    ```bash
    kubectl describe node <some-node-name> --show-events=true
    ```

### Kubernetes pod events and status

```{tip}
The following commands require passing the namespace where a specific pod is running. Usually this namespace is the same with the hub name.
```

1. Running pods in a namespace and their status
    ```bash
    kubectl get pods -n <namespace>
    ```

2. Running pods in all namespaces of the cluster and their status
    ```bash
    kubectl get pods --all-namespaces
    ```

3. Get a pod's events from the past 1h
    ```bash
    kubectl get events --field-selector involvedObject.kind=Pod --field-selector involvedObject.name=<some-pod-name>
    ```

4. Describe a pod and any related events
    ```bash
    kubectl describe pod <some-pod-name> --show-events=true
    ```

### Kubernetes pod logs
You can access any pod's logs by using the `kubectl logs` commands. Below are some of the most common debugging commands.

```{tip}
1. The `--follow` flag

   You can pass the `--follow` flag to each of the `kubectl logs` command below to stream the logs as they are happening, otherwise, they will just be presented up to the current point in time and then stop.

2. The `--previous` flag

   If the pod has restarted due to an error, you can pass `--previous` to look at the logs of the pod prior to the last restart.

3. The `--tail` flag

    With `--tail=<number>` flag you can pass the number of lines of recent log file to display, otherwise, it will show all log lines.

4. The `--since` flag

    This flag can be used like `--since=1h` to only return logs newer than 1h in this case, or any other relative duration like 5s, 2m, or 3h.
```

1. Print the logs of a pod
    ```bash
    kubectl logs <pod_name> --namespace <pod_namespace>
    ```

2. Print the logs for a container in a pod
    ```bash
    kubectl logs -c <container_name> <pod_name> --namespace <pod_namespace>
    ```

3. View the logs for a previously failed pod
    ```bash
    kubectl logs --previous <pod_name> --namespace <pod_namespace>
    ```

4. View the logs for all containers in a pod
    ```bash
    kubectl logs <pod_name> --all-containers --namespace <pod_namespace>
    ```