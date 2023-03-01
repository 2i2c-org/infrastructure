# Access home directories of users of a hub

Sometimes, it is necessary to access the NFS home directories of users on a hub.
Perhaps they've modified a dotfile (like `.bash_profile` or `.bashrc`) that prevents their
server from starting, or we need to archive a large file there.

Sample notebook log from non-starting pod due to a dotfile that doesn't have correct `PATH`:w

```
/srv/start: line 23: exec: jupyterhub-singleuser: not found
```

The
[`exec-homes-shell`](https://github.com/2i2c-org/infrastructure/blob/master/deployer/README.md#exec-homes-shell)
subcommand of the deployer can help us here.

```bash
export CLUSTER_NAME=<cluster-name>
export HUB_NAME=<hub-name>
```

```bash
deployer exec-homes-shell $CLUSTER_NAME $HUB_NAME
```

Will open a bash shell with all the home directories of all the users of `$HUB_NAME`
in `$CLUSTER_NAME  ` mounted in read-write fashion under `/home/`.

```{warning}
BE CAREFUL! DO NOT DELETE THINGS HERE WITHOUT BEING SURE YOU WANT THEM GONE.

If in doubt, **rename files** which will allow the server to start up again and preserve the file for the user so they can correct the file contents.
```
