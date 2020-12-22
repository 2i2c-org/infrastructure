import backoff
from copy import deepcopy
import hashlib
import subprocess
import hmac
import os
import json
import tempfile
from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError
from textwrap import dedent
from build import last_modified_commit
from contextlib import contextmanager
from build import build_image
from jupyterhub_client.execute import execute_notebook

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ='safe', pure=True)

@contextmanager
def decrypt_file(encrypted_path):
    """
    Provide secure temporary decrypted contents of a given file

    If file isn't a sops encrypted file, we assume no encryption is used
    and return the current path.
    """
    # We must first determine if the file is using sops
    # sops files are JSON/YAML with a `sops` key. So we first check
    # if the file is valid JSON/YAML, and then if it has a `sops` key
    with open(encrypted_path) as f:
        _, ext = os.path.splitext(encrypted_path)
        # Support the (clearly wrong) people who use .yml instead of .yaml
        if ext == '.yaml' or ext == '.yml':
            try:
                encrypted_data = yaml.load(f)
            except ScannerError:
                yield encrypted_path
                return
        elif ext == '.json':
            try:
                encrypted_data = json.load(f)
            except json.JSONDecodeError:
                yield encrypted_path
                return

    if 'sops' not in encrypted_data:
        yield encrypted_path
        return

    # If file has a `sops` key, we assume it's sops encrypted
    with tempfile.NamedTemporaryFile() as f:
        subprocess.check_call([
            'sops',
            '--output', f.name,
            '--decrypt', encrypted_path
        ])
        yield f.name

class Cluster:
    """
    A single k8s cluster we can deploy to
    """
    def __init__(self, spec):
        self.spec = spec
        self.hubs = [
            Hub(self, hub_yaml)
            for hub_yaml in self.spec['hubs']
        ]

    def build_image(self):
        build_image(self.spec['image_repo'])

    @contextmanager
    def auth(self):
        with tempfile.NamedTemporaryFile() as kubeconfig:
            # FIXME: This is dumb
            os.environ['KUBECONFIG'] = kubeconfig.name
            assert self.spec['provider'] == 'gcp'

            yield from self.auth_gcp()

    def auth_gcp(self):
        config = self.spec['gcp']
        key_path = config['key']
        project = config['project']
        # If cluster is regional, it'll have a `region` key set.
        # Else, it'll just have a `zone` key set. Let's respect either.
        location = config.get('zone', config.get('region'))
        cluster = config['cluster']

        with decrypt_file(key_path) as decrypted_key_path:
            subprocess.check_call([
                'gcloud', 'auth',
                'activate-service-account',
                '--key-file', os.path.abspath(decrypted_key_path)
            ])

        subprocess.check_call([
            'gcloud', 'container', 'clusters',
            # --zone works with regions too
            f'--zone={location}',
            f'--project={project}',
            'get-credentials', cluster
        ])

        yield


class Hub:
    """
    A single, deployable JupyterHub
    """
    def __init__(self, cluster, spec):
        self.cluster = cluster
        self.spec = spec

        self.nfs_share_name = f'/export/home-01/homes/{self.spec["name"]}'

    def get_generated_config(self, auth_provider, proxy_secret_key):
        """
        Generate config automatically for each hub

        Some config should be automatically set for all hubs based on
        spec in hubs.yaml. We generate them here.

        WARNING: CONTAINS SECRET VALUES!
        """

        proxy_secret = hmac.new(proxy_secret_key, self.spec['name'].encode(), hashlib.sha256).hexdigest()

        generated_config = {
            'nfsPVC': {
                'nfs': {
                    'shareName': self.nfs_share_name,
                }
            },
            'jupyterhub': {
                'proxy': { 'secretToken': proxy_secret },
                'ingress': {
                    'hosts': [self.spec['domain']],
                    'tls': [
                        {
                            'secretName': f'https-auto-tls',
                            'hosts': [self.spec['domain']]
                        }
                    ]

                },
                'singleuser': {
                    'image': {
                        'name': self.cluster.spec['image_repo']
                    },
                },
                'hub': {
                    'initContainers': [
                        {
                            'name': 'templates-clone',
                            'image': 'alpine/git',
                            'args': [
                                'clone',
                                '--',
                                'https://github.com/2i2c-org/pilot-homepage',
                                '/srv/repo',
                            ],
                            'securityContext': {
                                'runAsUser': 1000,
                                'allowPrivilegeEscalation': False,
                                'readOnlyRootFilesystem': True,
                            },
                            'volumeMounts': [
                                {
                                    'name': 'custom-templates',
                                    'mountPath': '/srv/repo'
                                }
                            ]
                        }
                    ],
                    'extraContainers': [
                        {
                            'name': 'templates-sync',
                            'image': 'alpine/git',
                            'workingDir': '/srv/repo',
                            'command': ['/bin/sh'],
                            'args': [
                                '-c',
                                dedent(
                                    f'''\
                                    while true; do git fetch origin;
                                    if [[ $(git ls-remote --heads origin {self.spec["name"]} | wc -c) -ne 0 ]]; then
                                        git reset --hard origin/{self.spec["name"]};
                                    else
                                        git reset --hard origin/master;
                                    fi
                                    sleep 5m; done
                                    '''
                                )
                            ],
                            'securityContext': {
                                'runAsUser': 1000,
                                'allowPrivilegeEscalation': False,
                                'readOnlyRootFilesystem': True,
                            },
                            'volumeMounts': [
                                {
                                    'name': 'custom-templates',
                                    'mountPath': '/srv/repo'
                                }
                            ]
                        }
                    ],
                    'extraVolumes': [
                        {
                            'name': 'custom-templates',
                            'emptyDir': {}
                        }
                    ],
                    'extraVolumeMounts':[
                        {
                            'mountPath': '/usr/local/share/jupyterhub/custom_templates',
                            'name': 'custom-templates',
                            'subPath': 'templates'
                        },
                        {
                            'mountPath': '/usr/local/share/jupyterhub/static/extra-assets',
                            'name': 'custom-templates',
                            'subPath': 'extra-assets'
                        }
                    ]
                }
            },
        }
        #
        # Allow explicilty ignoring auth0 setup
        if self.spec['auth0'].get('enabled', True):
            client = auth_provider.ensure_client(
                self.spec['name'],
                self.spec['domain'],
                self.spec['auth0']['connection']
            )
            generated_config['jupyterhub']['auth'] = auth_provider.get_client_creds(client, self.spec['auth0']['connection'])

        return self.apply_hub_template_fixes(generated_config, proxy_secret_key)


    def setup_nfs_share(self):
        """
        Create the NFS Share used for user home directories

        Instead of mounting the directory containing *all* hubs' home directories and then using
        `subDir` to make just the user's directory visible to them, we want to mount the directory
        containing *just* the home directories of users on this hub. To do so, we must create the
        directory before the user pods can start - since otherwise there's no NFS share to mount.
        """
        # FIXME: This should be provider agnostic
        zone = self.cluster.spec['gcp']['nfs']['zone']
        project = self.cluster.spec['gcp']['project']
        # WARNING: This needs to be idempotent, so watch what you do here.
        # WARNING: This is a very highly privileged operation, so be careful when you touch this.
        subprocess.check_call([
            'gcloud', 'compute', 'ssh', 'nfs-server-01', '--zone', zone, '--project', project, '--',
            f'sudo mkdir -p {self.nfs_share_name} && sudo chown 1000:1000 {self.nfs_share_name} && sudo ls -ld {self.nfs_share_name}'
        ])

    def failure_handler(details):
        print(f"Hub check health validation failed {details['tries']} times, hub not healthy. Stopping further deployments")
    def success_handler(details):
        print(f"Hub health validation finished successfully. Hub is healthy!")

    # Try 2 times before declaring it a failure
    @backoff.on_exception(
        backoff.expo,
        ValueError,
        on_success=success_handler,
        on_giveup=failure_handler,
        max_tries=2
    )
    async def check_hub_health(self, test_notebook_path, service_api_token):
        """
        After each hub gets deployed, validate that it 'works'.

        Automatically create a temporary user, start their server and run a test notebook, making
        sure it runs to completion. Stop and delete the test server at the end. Try this steps twice
        before declaring it a failure. If any of these steps fails, immediately halt further
        deployments and error out.
        """
        hub_url = f'https://{self.spec["domain"]}'
        # Export the hub health check service as an env var so that jupyterhub_client can read it.
        os.environ['JUPYTERHUB_API_TOKEN']=service_api_token

        await execute_notebook(
            hub_url,
            test_notebook_path,
            temporary_user=True,
            create_user=True,
            delete_user=True
        )

    def apply_hub_template_fixes(self, generated_config, proxy_secret_key):
        """
        Modify generated_config based on what hub template we're using.

        Different hub templates require different pre-set config. For example,
        anything deriving from 'base-hub' needs all config to be under a 'base-hub'
        config. dask hubs require apiTokens, etc.

        Ideally, these would be done declaratively. Untile then, let's put all of
        them in this function.
        """
        hub_template = self.spec['template']

        # Generate a token for the hub health service
        hub_health_token = hmac.new(proxy_secret_key, 'health-'.encode() + self.spec['name'].encode(), hashlib.sha256).hexdigest()
        # Describe the hub health service
        generated_config['jupyterhub']['hub'] = {
            'services': {
                'hub-health': {
                    'apiToken': hub_health_token,
                    'admin': True
                }
            }
        }

        # FIXME: Have a templates config somewhere? Maybe in Chart.yaml
        # FIXME: This is a hack. Fix it.
        if hub_template != 'base-hub':
            generated_config = {
                'base-hub': generated_config
            }

        # LOLSOB FIXME
        if hub_template == 'daskhub':
            gateway_token = hmac.new(proxy_secret_key, 'gateway-'.encode() + self.spec['name'].encode(), hashlib.sha256).hexdigest()
            generated_config['dask-gateway'] = {
                'gateway': {
                    'auth': {
                        'jupyterhub': { 'apiToken': gateway_token }
                    }
                }
            }
            generated_config['base-hub']['jupyterhub']['hub']['services'] = {
                'dask-gateway': { 'apiToken': gateway_token }
            }

        return generated_config

    async def deploy(self, auth_provider, proxy_secret_key, test_notebook_path=None):
        """
        Deploy this hub
        """

        generated_values = self.get_generated_config(auth_provider, proxy_secret_key)

        # FIXME: Don't do this for ephemeral hubs
        self.setup_nfs_share()

        with tempfile.NamedTemporaryFile() as values_file, tempfile.NamedTemporaryFile() as generated_values_file:
            yaml.dump(self.spec['config'], values_file)
            yaml.dump(generated_values, generated_values_file)
            values_file.flush()
            generated_values_file.flush()

            cmd = [
                'helm', 'upgrade', '--install', '--create-namespace', '--wait',
                '--namespace', self.spec['name'],
                self.spec['name'], os.path.join('hub-templates', self.spec['template']),
                # Ordering matters here - config explicitly mentioned in `hubs.yaml` should take
                # priority over our generated values. Based on how helm does overrides, this means
                # we should put the config from hubs.yaml last.
                '-f', generated_values_file.name,
                '-f', values_file.name,
            ]

            print(f"Running {' '.join(cmd)}")
            subprocess.check_call(cmd)

            if test_notebook_path:
                try_idx = 1
                if self.spec['template'] != 'base-hub':
                    service_api_token = generated_values["base-hub"]["jupyterhub"]["hub"]["services"]["hub-health"]["apiToken"]
                else:
                    service_api_token = generated_values["jupyterhub"]["hub"]["services"]["hub-health"]["apiToken"]
                await self.check_hub_health(test_notebook_path, service_api_token)
