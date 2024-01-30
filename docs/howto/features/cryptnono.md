(howto:features:cryptnono)=
# Enable stronger anti-crypto abuse features for a hub

For JupyterHubs and BinderHubs that are broadly open to the public, cryptomining
attacks are the most common security threat. They take up resources and rack up
cloud costs. While most hubs can get away with gating access to them via some
kind of login restriction, for a subset of hubs this is not ideal (for equity and
access reasons).

For those cases, we enable a stronger deployment of [cryptnono](https://github.com/cryptnono/cryptnono).
The cryptnono project (in use on mybinder.org as well) helps detect and kill cryptominers via
various 'Detectors'.

## Detectors

Cryptnono currently has two primary detectors:

1. A detector for the [monero](https://www.getmonero.org/) cryptocurrency, that is based on
   official guidance [from the monero project](https://blog.px.dev/detect-monero-miners/) on
   how to detect it. This is fairly safe and has a very low false positive rate, and requires
   no configuration. So by default, **this detector is enabled on all hubs**.

2. A detector (`execWhacker`) based on heuristics, where the full commandline used to execute a process (
   regardless of how it is started) is used to detect if a process is likely crypto mining,
   and if so, immediately kill it. This relies on a tweakable config of banned strings to
   look for in the commandline of a process, and is [constantly being tweaked](https://github.com/jupyterhub/mybinder.org-deploy/security/advisories/GHSA-j42g-x8qw-jjfh).
   Since making the list of banned strings public would make ban evasion easy, the list of
   strings (and the method used to generate them) is encrypted. You can read more details
   about the specific method used by looking in the encrypted code file (`deployer/commands/generate/cryptnono_config/encrypted_secret_blocklist.py`)
   in this repository.

   Since this detector may have a non-0 false positive rate, it is currently *not* enabled by
   default. However, eventually, once the config matures enough (and we have tested it enough),
   this would also be enabled by default everywhere. In the meantime, we only enable it for
   *clusters* with any hub that allows unfettered external access.

## Enabling the `execWhacker` detector

The `execWhacker` detector can be enabled with the following configuration in the appropriate
`support.values.yaml` for the cluster:

```yaml
cryptnono:
  detectors:
    # Enable execwhacker, as this cluster has a hub that is widely open to the public
    execwhacker:
      enabled: true
```

Upon deployment of this change, you can verify the detector is enabled by looking for a container
named `execwhacker` in the `cryptnono` daemonset in the `support` namespace.

```yaml
kubectl -n support get daemonset support-cryptnono -o yaml
```

## Testing the `execWhacker` detector

To test that the detector is actually working, you can login to a hub on the cluster and
try to execute the following command:

```bash
ls phahPaiWie2aeluax4Of7tiwiekujeaF7aquuPeexeiT7jieJailaKai7haiB0raetib9ue8Ai2daeTaehaemohJeeyaifeip6nevae5Safeir9iep8Baic3nohn9zoa
```

It should immediately die, with a message saying `Killed`. This is a randomly generated test string, set up
in an unencrypted fashion in `helm-charts/support/values.yaml` under `cryptnono.detectors.execwhacker.configs`,
to enable testing by engineers and others.

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
    --field-selector spec.nodeName=<name-of-node>\
    -l app.kubernetes.io/name=cryptnono
   ```

   This should show *just* the cryptnono pod running on the node in which the user server in question was running.

3. Look at the logs on that pod with `kubectl logs`:

   ```bash
   kubectl -n support logs <pod-name> -c execwhacker
   ```

   The logs will be structured as `json`, and will look like this:

   ```json
   {"pid": 13704, "cmdline": "/usr/bin/ls --color=auto phahpaiwie2aeluax4of7tiwiekujeaf7aquupeexeit7jiejailakai7haib0raetib9ue8ai2daetaehaemohjeeyaifeip6nevae5safeir9iep8baic3nohn9zoa", "matched": "phahpaiwie2aeluax4of7tiwiekujeaf7aquupeexeit7jiejailakai7haib0raetib9ue8ai2daetaehaemohjeeyaifeip6nevae5safeir9iep8baic3nohn9zoa", "source": "execwhacker.bpf", "action": "killed", "event": "Killed process", "level": "info", "timestamp": "2024-01-30T19:35:36.610659Z"}
   ```

   This tells us that the name of the process, as well as why it was killed.

   ```{note}
   We will eventually be able to see the [pod & namespace](https://github.com/cryptnono/cryptnono/issues/30) information
   of killed processes as well.
   ```

   ```{tip}
   To make the JSON easier to read, you can pipe the logs command to `jq`.
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
documentation in `encrypted_secret_blocklist.py`, but how does one hack on it?

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

## Right to Replicate considerations

2i2c's [Right to Replicate](https://2i2c.org/right-to-replicate/) guarantees that communities can leave
with their hubs whenever they please, without any secret sauce. Cryptnono has two pieces of secret info
here:

1. The script to generate the secret config.
2. The secret config itself.

If a community wishes to leave and needs the config, we can make sure they know what the config is and
how to keep it updated - very similar to how we would handle passing on CILogon credentials or similar to
them. Since none of the code for cryptnono itself is secret, this does not conflict with right to replicate.

## Future work

`cryptnono` also exposes prometheus metrics about processes it has killed. We currently do not collect these,
but we should enable collection so we can
