# Initial timeboxed (30m) ticket resolution checklist

In the [non-incident support response process](https://compass.2i2c.org/projects/managed-hubs/support/#non-incident-response-process), an initial 30m timeboxed ticket resolution process is documented.

The support triagers use these 30m time interval to try an resolve a ticket, before opening a follow-up issue about it.

The next sections represents an incomplete initial checklist that the support triager can follow in order to resolve the ticket or decide on opening a tracking issue about it, with the context they gained during this investigation.

The steps to follow depend greatly on the type of ticket. To simplify, only three big ticket categories will be addressed.

```{list-table} Category 1: [](something-is-not-working)
:name: steps-table
:widths: 30 30
:header-rows: 1

*   - [](something-is-not-working:app-logs)
    - [](something-is-not-working:infra-logs)
*   - ☑[](something-is-not-working:app-logs:check-component)
    - ☑[](something-is-not-working:infra-logs:via-kubectl)
*   - ☑[](something-is-not-working:app-logs:check-user)
    - ☑[](something-is-not-working:infra-logs:via-ui)
```

```{list-table} Category 2: [](new-feature-request)
:widths: 30
:header-rows: 1

*   - Is the feature requested documented at [](hub-features)?
*   - ☑ Yes? Then enable it after checking it is in the scope of the contract.
*   - ▫️ No? Then open a GitHub tracking issue about it and continue following the non-incident process.
```


```{list-table} Category 3: [](technical-advice)
:widths: 30
:header-rows: 1

*   - Is the question about an area where the support triager has insight into?
*   - ☑ Yes? Then answer the ticket.
*   - ▫️ No? Then open a GitHub tracking issue about it and continue following the non-incident process
```

(something-is-not-working)=
## Something is not working

````{important}
If something is not working, you might be dealing with an incident, so depending on the scale of the issue and its nature, you might want to consider following the [Incident Response Process](https://compass.2i2c.org/projects/managed-hubs/incidents/#incident-response-process).

```{list-table} Checklist when something is not working if not an incident
:widths: 30
:header-rows: 0
*   - ☑ ask any additional info
*   - ☑ [check the logs](#steps-table)
*   - ☑ save the ones that look "interesting"
*   - ☑ identify if it's any of the issues described at [](troubleshooting)
```
````

(something-is-not-working:app-logs)=
### Check the logs at the application level

Get the name of the cluster and hub you want to debug and export their names as env vars. Example:

```bash
export CLUSTER_NAME=2i2c; export HUB_NAME=staging
```

```{note}
You can pass `--no-follow` to each of the commands below to provide just logs up to the current point in time and then stop. If the pod has restarted due to an error, you can pass `--previous` to look at the logs of the pod prior to the last restart.
```
(something-is-not-working:app-logs:check-component)=
#### Component logs

Get the logs of each component or the ones you suspect might have useful info

```bash
deployer debug component-logs $CLUSTER_NAME $HUB_NAME hub
```

```bash
deployer debug component-logs $CLUSTER_NAME $HUB_NAME proxy
```

```bash
deployer debug component-logs $CLUSTER_NAME $HUB_NAME dask-gateway-api
```

```bash
deployer debug component-logs $CLUSTER_NAME $HUB_NAME dask-gateway-controller
```

```bash
deployer debug component-logs $CLUSTER_NAME $HUB_NAME traefik
```

(something-is-not-working:app-logs:check-user)=
#### User logs

Display logs from the notebook pod of a given user:

```bash
deployer debug user-logs  $CLUSTER_NAME $HUB_NAME <username>
```

(something-is-not-working:infra-logs)=
### Check the logs at the infrastructure level

(something-is-not-working:infra-logs:via-kubectl)=
#### Using `kubectl`

1. Authenticate into the desired cluster using the deployer's credentials and pop a new shell there.

    ```bash
    deployer use-cluster-credentials $CLUSTER_NAME
    ```

2. Execute the desired `kubectl` commands into this shell

  - Get current running nodes and their status
    ```bash
    kubectl get nodes
    ```
  - Get the most important events in a given namespace
    ```bash
    kubectl get events -n <namespace>
    ```
  - Get the most important events in all namespaces of the cluster
    ```bash
    kubectl get events --all-namespaces
    ```
  - Get all the running pods in a namespace and their status
    ```bash
    kubectl get pods -n <namespace>
    ```
  - Get all the running pods in all namespaces of the cluster
    ```bash
    kubectl get pods --all-namespaces
    ```

(something-is-not-working:infra-logs:via-ui)=
#### [Accessing the cloud provider's UI](howto-troubleshoot:cloud-logs).

(new-feature-request)=
## New feature requested

```{important}
Q: Is the feature something that already exist and documented at [](hub-features)?
A: Yes? Then enable it after checking it is in the scope of the contract.
```

(technical-advice)=
## Technical advice

```{important}
Q: Is the question about an area where the support triager has insight into?
A: Yes? Then answer the ticket
   No? Then open a GitHub tracking issue about it and continue following the non-incident process.
```
