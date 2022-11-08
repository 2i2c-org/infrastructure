# Access home directories of users of a hub

Sometimes, it is necessary to access the home directories of users on a hub.
Perhaps they've modified a dotfile (like `.bash_profile`) that prevents their
server from starting, or we need to archive a large file there.

The
[`exec-homes-shell`](https://github.com/2i2c-org/infrastructure/blob/master/deployer/README.md#exec-homes-shell)
subcommand of the deployer can help us here.

```bash
python3 deployer.debug exec-homes-shell <cluster-name> <hub-name>
```

Will open a bash shell with all the home directories of all the users of `<hub-name>`
in `<cluster-name>` mounted in read-write fashion under `/home/`.

```{warning}
BE CAREFUL! DO NOT DELETE THINGS HERE WITHOUT BEING SURE YOU WANT THEM GONE.

If in doubt, **rename files** which will allow the server to start up again and preserve the file for the user so they can correct the file contents.
```