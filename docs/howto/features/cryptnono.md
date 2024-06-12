(howto:features:cryptnono)=
# Enable stronger anti-crypto abuse features for a hub

These docs discuss how to test and work on the `execwhacker` detector. It is enabled
on *all* our hubs, but is particularly useful for hubs that are open to the world.
Cryptomining attacks are the most common security threat to these hubs, as
they take up resources and rack up cloud bills.

These docs also cover:
- how to test if `execWhacker` is operational,
- regenerating the list of banned strings used by `execwhacker`, and
- how to work on the encrypted banned strings generator script.

```{note}
For more information on `cryptnono`, it's use, and the detectors, please see
[](topic:cryptnono) and <https://github.com/cryptnono/cryptnono>.
```

## Testing the `execwhacker` detector

To test that the detector is actually working, you can login to a hub on the cluster and
try to execute the following command:

```bash
sh -c 'sleep 1 && echo beiquatohGa1uay0ahMies9couyahPeiz9xohju3Ahvaik3FaeM7eey1thaish1U'
```

It should immediately die, with a message saying `Killed`. This is a randomly generated test string, set up
in an unencrypted fashion in `helm-charts/support/values.yaml` under `cryptnono.detectors.execwhacker.configs`,
to enable testing by engineers and others. We also put the `sleep` in there as it can sometimes take cryptnono
upto a second to kill a process.

## Looking at logs to understand why a process was killed by `execwhacker`

Cryptnono is deployed as a [daemonset](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/),
so there should be one pod per node deployed. It will log each process it kills, why it kills them, and if it
intentionally spares a process, why as well. So if a process is being killed due to this, you can look at logs
to understand why - it may also lead to more tweaking of the generator config.

1. Find the *node* in which the user server is running.

   ```bash
   kubectl -n <hub-name> get pod -o wide
   ```

   The `-o wide` will add an additional column, `NODE`, showing which node the pods are running in. Find the
   node of the user pod you care about.

2. Find the appropriate `cryptnono` pod for this node.

   ```bash
   kubectl -n support get pod \
    --field-selector spec.nodeName=<name-of-node> \
    -l app.kubernetes.io/name=cryptnono
   ```

   This should show *just* the cryptnono pod running on the node in which the user server in question was running.

3. Look at the logs on that pod with `kubectl logs`:

   ```bash
   kubectl -n support logs <pod-name> -c execwhacker
   ```

   The logs will be structured as `json`, and will look like this:

   ```json
    {
        "pid": 23933,
        "cmdline": "/usr/bin/sh -c 'sleep 1 && echo beiquatohga1uay0ahmies9couyahpeiz9xohju3ahvaik3faem7eey1thaish1u'",
        "matched": "beiquatohga1uay0ahmies9couyahpeiz9xohju3ahvaik3faem7eey1thaish1u",
        "source": "execwhacker.bpf",
        "container_type": "cri",
        "labels": {
            "io.kubernetes.container.name": "notebook",
            "io.kubernetes.pod.name": "jupyter-921a1d97-2d4cb1-2d4eb1-2da427-2dd5eed98e3ab9",
            "io.kubernetes.pod.namespace": "spyglass",
            "io.kubernetes.pod.uid": "d2ed6416-812f-413b-ba53-e62d11646809"
        },
        "image": "quay.io/2i2c/hhmi-spyglass-image:67523d9ea855",
        "action": "killed",
        "event": "Killed process",
        "level": "info",
        "timestamp": "2024-01-31T16:59:32.990489Z"
    }
   ```

   This tells us that the name of the process, the name of the pod (and hence user) who was cryptomining, the
   namespace (and hence hub name) it happened in, the image being used as well as what string was matched that
   caused it to die.

   ```{tip}
   The logs by default output one JSON object per line, which is hard for a human to read. You can pipe it
   to `jq` to make it easier to read!
   ```

## Regenerating list of banned strings

Periodically, we will have to regenerate the list of banned strings to tune `cryptnono`,
by running the following command:

```bash
deployer generate cryptnono-secret-config
```

This will update the file `helm-charts/support/enc-cryptnono.secret.values.yaml` and re-encrypt it.

## Working on the banned strings generator

The banned strings generator is a fairly simple python script, present in `deployer/commands/generate/cryptnono_config/enc-blocklist-generator.secret.py`.
It's unencrypted and loaded by code in `deployer/commands/generate/cryptnono_config/__init__.py`. There is inline
documentation in `enc-blocklist-generator.secret.py`, but how does one maintain it?

1. Unencrypt the file with `sops`

   ```bash
    sops --decrypt deployer/commands/generate/cryptnono_config/enc-blocklist-generator.secret.py > deployer/commands/generate/cryptnono_config/blocklist-generator.secret.py
   ```

   This will create `deployer/commands/generate/cryptnono_config/blocklist-generator.secret.py` (which is in `.gitignore` and hence
   can not be committed accidentally) with the unencrypted code.

   ```{note}

   Because this file is in `.gitignore`, your IDE may not show it to when you search for files by default!
   ```

2. Work on the code as you wish - it's just a regular python file.

3. Re-encrypt it with `sops`

   ```bash
    sops --encrypt deployer/commands/generate/cryptnono_config/blocklist-generator.secret.py > deployer/commands/generate/cryptnono_config/enc-blocklist-generator.secret.py
   ```

4. Run `deployer generate cryptnono-secret-config` to test.
