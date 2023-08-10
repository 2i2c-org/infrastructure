# Setup a database server per user

We can support providing a single, isolated database *server* per user. This
is extremely helpful for teaching cases, as users can do whatever they want with
their server without affecting other users.

## Setting up the backing disk for the database

Each database server needs a backing disk to store its data. We have custom code in
our `basehub/values.yaml` that creates arbitrary extra disks per user that can be used.

```yaml
jupyterhub:
  custom:
    singleuser:
      extraPVCs:
        - name: postgres-{username}
          class: standard
          capacity: 1Gi
```

This will create an additional Kubernetes [Persistent Volume Claim](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
per user, named `postgres-<name-of-user>`, created with Kubernetes [Storage
Class](https://kubernetes.io/docs/concepts/storage/storage-classes/), and capacity of
`1Gi` (remember it is `1Gi`, not `1G`!).

You can get the list of storageclasses available in the target cluster with a
`kubectl get storageclass`. On AWS, the two options generally available are
`gp2` (standard spinning disk) and `ssd` (faster, more expensive SSD). On GKE, the two options
are `standard` (spinning disk), `standard-rwo` ("balanced" disk) and `premium-rwo` (SSD disk).

`capacity` can be increased later on if needed and kubernetes will
[automatically resize](https://kubernetes.io/blog/2018/07/12/resizing-persistent-volumes-using-kubernetes/) the disk
when users start / stop the server. However, the storage class *can not* be changed
afterwards - so users will have to decide if they want spinning disks (slower, chepeaper)
or ssd disks (faster, much more expensive) at the start.

## Setup the database server

We can then run the database server (such as postgres) as a [sidecar
container](https://www.containiq.com/post/kubernetes-sidecar-container). This will
run one server per user with a config we provide, and use the backing disk we have created
for the user in the previous section. The configuration for server needs to be specific
to the kind of database we are running.

### Postgres

The following config can be used to setup a postgres db container as a sidecar per-user.
Tweak the config as necessary for the specific hub's needs.

```yaml
jupyterhub:
  singleuser:
    initContainers:
      # /var/lib/postgresql should be writeable by uid 1000, so students
      # can blow out their db directories if need to.
      # We have to chown /home/jovyan and /home/jovyan/shared-readwrite as well -
      # since initContainers is a list, setting this here overwrites the chowning
      # initContainer we have set in basehub/values.yaml
      - name: volume-mount-ownership-fix
        image: busybox
        command:
            [
                "sh",
                "-c",
                "id && chown 1000:1000 /home/jovyan && chown 1000:1000 /home/jovyan/shared && chown 1000:1000 /var/lib/postgresql/data && ls -lhd /home/jovyan ",
            ]
        securityContext:
            runAsUser: 0
        volumeMounts:
          - name: home
            mountPath: /home/jovyan
            subPath: "{username}"
          # Mounted without readonly attribute here,
          # so we can chown it appropriately
          - name: home
            mountPath: /home/jovyan/shared
            subPath: _shared
          - name: postgres-db
            mountPath: /var/lib/postgresql/data
            # postgres recommends against mounting a volume directly here
            # So we put data in a subpath
            subPath: data
    storage:
      extraVolumes:
        - name: postgres-db
          persistentVolumeClaim:
            # This should match what is set as `name` in the earlier step under `custom.singleuser.extraPVCs`
            claimName: 'postgres-{username}'
      extraVolumeMounts:
        - name: postgres-db
          mountPath: /var/lib/postgresql/data
          # postgres recommends against mounting a volume directly here
          # So we put data in a subpath
          subPath: data
    extraContainers:
      - name: postgres
        image: postgres:14.5 # use the latest version available at https://hub.docker.com/_/postgres/tags
        args:
          # Listen only on localhost, rather than on all interfaces
          # This allows us to use passwordless login, as only the user notebook container can access this
          - -c
          - listen_addresses=127.0.0.1
        resources:
          limits:
            # Best effort only. No more than 1 CPU, and if postgres uses more than 512M, restart it
            memory: 512Mi
            cpu: 1.0
          requests:
            # If we don't set requests, k8s sets requests == limits!
            # So we set something tiny
            memory: 64Mi
            cpu: 0.01
        env:
          # Configured using the env vars documented in https://hub.docker.com/_/postgres/
          # Postgres is only listening on localhost, so we can trust all connections that come to it
          - name: POSTGRES_HOST_AUTH_METHOD
            value: "trust"
          # The name of the default user in our user image is jovyan, so the postgresql superuser
          # should also be called that
          - name: POSTGRES_USER
            value: "jovyan"
          securityContext:
            runAsUser: 1000
          volumeMounts:
          # Mount the user homedirectory in the postgres db container as well, so postgres commands
          # that load data into the db from disk work
          - name: home
            mountPath: /home/jovyan
            subPath: "{username}"
          - name: postgres-db
            mountPath: /var/lib/postgresql/data
            # postgres recommends against mounting a volume directly here
            # So we put data in a subpath
            subPath: data
```

## Cleanup created disks after use

If the per-user db is no longer needed, we should cleanup the created disks
so we are no longer charged for them. Just deleting the Kubernetes PVCs
created here should delete the underlying disks as well. 

```{warning}
This is irreversible! Make sure the community is fully aware before doing this
```

1. Get the list of PVCs created with this feature:

   ```bash
   kubectl -n <namespace> get pvc -l component=extra-pvc
   ```
   
   Inspect it to make sure you are deleting the PVCs **from the right hub**
   from the **right cluster**.
   
2. Delete the PVCs:

   ```bash
   kubectl -n <namespace> delete pvc -l component=extra-pvc
   ```
   
   This might take a while. The backing disks will be deleted by Kubernetes as well,
   once any pods attached to them go down. This means it is safe to run this
   command while users are currently running - there will be no effects on
   any running user pods!
   
