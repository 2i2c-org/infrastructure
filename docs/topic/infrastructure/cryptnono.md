(topic:cryptnono)=
# Cryptnono for preventing cryptomining abuse

For JupyterHubs and BinderHubs that are broadly open to the public, cryptomining
attacks are the most common security threat. They take up resources and rack up
cloud costs. While most hubs can get away with gating access to them via some
kind of login restriction, for a subset of hubs this is not ideal (for equity and
access reasons).

For those cases, we enable a stronger deployment of [cryptnono](https://github.com/cryptnono/cryptnono).
The cryptnono project (in use on mybinder.org as well) helps detect and kill cryptominers via
various 'Detectors'.

(topic:cryptnono:detectors)=
## Detectors

Cryptnono currently has two primary detectors:

1. A detector for the [monero](https://www.getmonero.org/) cryptocurrency, that is based on
   official guidance [from the monero project](https://blog.px.dev/detect-monero-miners/) on
   how to detect it. This is fairly safe and has a very low false positive rate, and requires
   no configuration. So by default, **this detector is enabled on all hubs**.

2. A detector (`execwhacker`) based on heuristics, where the full commandline used to execute a process (
   regardless of how it is started) is used to detect if a process is likely crypto mining,
   and if so, immediately kill it. This relies on a tweakable config of banned strings to
   look for in the commandline of a process, and is [constantly being tweaked](https://github.com/jupyterhub/mybinder.org-deploy/security/advisories/GHSA-j42g-x8qw-jjfh).
   Since making the list of banned strings public would make ban evasion easy, the list of
   strings (and the method used to generate them) is encrypted. You can read more details
   about the specific method used by looking in the encrypted code file (`deployer/commands/generate/cryptnono_config/encrypted_secret_blocklist.py`)
   in the `infrastructure` repository.

   Since this detector may have a non-0 false positive rate, it is currently *not* enabled by
   default. However, eventually, once the config matures enough (and we have tested it enough),
   this would also be enabled by default everywhere. In the meantime, we only enable it for
   *clusters* with any hub that allows unfettered external access.

(topic:cryptnono:r2r)=
## Right to Replicate considerations

2i2c's [Right to Replicate](https://2i2c.org/right-to-replicate/) guarantees that communities can leave
with their hubs whenever they please, without any secret sauce. Cryptnono has two pieces of secret info
here:

1. The script to generate the secret config.
2. The secret config itself.

If a community wishes to leave and needs the config, we can make sure they know what the config is and
how to keep it updated - very similar to how we would handle passing on CILogon credentials or similar to
them. Since none of the code for cryptnono itself is secret, this does not conflict with right to replicate.

(topic:cryptnono:future)=
## Future work

`cryptnono` also exposes prometheus metrics about processes it has killed. We currently *do* collect these,
but there is no Grafana dashboard that exposes them yet.