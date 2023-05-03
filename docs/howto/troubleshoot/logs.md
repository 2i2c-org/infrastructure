# Look at logs to troubleshoot issues

Looking at and interpreting logs produced by various components is the easiest
way to debug most issues, and should be the first place to look at when issues
are reported. 

This page describes how to look at various logs in different cloud providers.

## Google Cloud Platform

On GCP, by default, all logs produced by all containers and other components
are sent to [Google Cloud Logging](https://cloud.google.com/logging). These
logs are kept for 30 days, and are searchable.

### Accessing the Logs Explorer

1. Go to [the log explorer](https://console.cloud.google.com/logs/query)
   on your browser.

2. Make sure **you are in the right project**, by looking at the project selector
   dropdown in the top bar, next to the 'Google Cloud' logo. If you are not in
   the correct project, switch to it before continuing

3. There is a query input textbox where you can write queries using the
   [Google Cloud Logging query language](https://cloud.google.com/logging/docs/view/logging-query-language),
   and get output. There is also a way to explore logs by resource type, as well
   as time sliders. However, for most of our logs, the 'log levels' (error, warning, etc)
   are not parsed correctly, and hence are useless.

4. Google provies a [query library](https://cloud.google.com/logging/docs/view/query-library) set of [sample queries](https://cloudlogging.app.goo.gl/Ad7B8hjFHpj6X7rT8) that you can access via the Library tab in Logs Explorer.


### Common queries

#### Kubernetes autoscaler logs

You can find scale up or scale down events by looking for decision events

```
logName="projects/<project-name>/logs/container.googleapis.com%2Fcluster-autoscaler-visibility" severity>=DEFAULT
jsonPayload.decision: *
```

#### Kubernetes node event logs for a particular node

```
resource.type="k8s_node"
log_id("events")
resource.labels.node_name="<node_name>"
```

#### Look at hub logs

The JupyterHub pod's logs can be fetched with the following query:

```
labels.k8s-pod/component="hub"
```

This gives logs of *all* containers in the hub pod in *all* namespaces in the
cluster. You can narrow it down to a particular namespace with:


```
labels.k8s-pod/component="hub"
resource.labels.namespace_name="<namespace>"
```


#### Look at a specific user's logs

You can look at *all* user pod logs from a given namespace with:

```
labels.k8s-pod/component="singleuser-server"
resource.labels.namespace_name="<namespace>"
```

To look at a specific user's pod logs:

```
labels.k8s-pod/component="singleuser-server"
labels.k8s-pod/hub_jupyter_org/username="<escaped-username>"
resource.labels.namespace_name="<namespace>"
```

(howto:troubleshoot:logs:username)=
Note that you need the *escaped* username, rather than just the username. You can
either spot it by taking a quick look at *all* the logs and finding out, or by
using the following python code snippet:

```python
import escapism
import string

username = "<your-username>"
escaped_username = escapism.escape(
    username, safe=set(string.ascii_lowercase + string.digits), escape_char="-"
).lower()
print(escaped_username)
```

```{tip}
Another super-quick shortcut is to replace any `-` in the username with `-2d`,
any `.` with `-2e` and any `@` with `-40`. If your username contains more
special characters, highly recommend using the script instead - escaping
errors can be frustrating!
```

#### Look at dask-gateway logs

The following query will show logs from all the components of dask-gateway -
the controller, API, proxy, individual schedulers and workers.

```
labels.k8s-pod/app_kubernetes_io/name="dask-gateway"
resource.labels.namespace_name="<namespace>"
```

To look at just the *scheduler* and *worker* logs of a specific user, you can
try:

```
labels.k8s-pod/app_kubernetes_io/name="dask-gateway"
resource.labels.namespace_name="<namespace>"
labels.k8s-pod/hub_jupyter_org/username="<escaped-username>"
```

You can also look by container name such as the below query for dask-worker and distributed.nanny. 

```
resource.type="k8s_container"
resource.labels.container_name="dask-worker" OR resource.labels.container_name="distributed.nanny"
```

You must pass the [escaped username](howto:troubleshoot:logs:username) to the
query.

#### Full-text search across logs

If you are looking for a specific string across *all* logs, you can
use `textPayload` or `jsonPayload` as a field to search for depending on the log.

```
textPayload=~"some-string"
```

This is most useful when *combined* with any of the other queries here. For
example, the following query will search across all user notebook pod logs:

```
labels.k8s-pod/component="singleuser-server"
resource.labels.namespace_name="<namespace>"
textPayload=~"some-string"
```
