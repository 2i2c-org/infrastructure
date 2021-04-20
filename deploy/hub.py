import backoff
from copy import deepcopy
import hashlib
import subprocess
import hmac
import os
import json
import pytest
import random
import tempfile
from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError
from textwrap import dedent
from build import last_modified_commit
from contextlib import contextmanager
from build import build_image
from jhub_client.execute import execute_notebook, JupyterHubAPI

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

    def get_generated_config(self, auth_provider, proxy_secret_key):
        """
        Generate config automatically for each hub

        Some config should be automatically set for all hubs based on
        spec in hubs.yaml. We generate them here.

        WARNING: CONTAINS SECRET VALUES!
        """

        proxy_secret = hmac.new(proxy_secret_key, self.spec['name'].encode(), hashlib.sha256).hexdigest()

        generated_config = {
            'jupyterhub': {
                'proxy': { 'secretToken': proxy_secret },
                'ingress': {
                    'hosts': self.spec['domain'] if isinstance(self.spec['domain'], list) else [self.spec['domain']],
                    'tls': [
                        {
                            'secretName': f'https-auto-tls',
                            'hosts': self.spec['domain'] if isinstance(self.spec['domain'], list) else [self.spec['domain']]
                        }
                    ]

                },
                'singleuser': {
                    # If image_repo isn't set, just have an empty image dict
                    'image': {'name': self.cluster.spec['image_repo']} if 'image_repo' in self.cluster.spec else {},
                },
                'hub': {
                    'config': {},
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
            # FIXME: We're hardcoding GenericOAuthenticator here
            # We should *not*. We need dictionary merging in code, so
            # these can all exist fine.
            generated_config['jupyterhub']['hub']['config']['GenericOAuthenticator'] = auth_provider.get_client_creds(client, self.spec['auth0']['connection'])

        return self.apply_hub_template_fixes(generated_config, proxy_secret_key)


    def unset_env_var(self, env_var, old_env_var_value):
        """
        If the old environment variable's value exists, replace the current one with the old one
        If the old environment variable's value does not exist, delete the current one
        """

        if env_var in os.environ:
            del os.environ[env_var]
        if (old_env_var_value is not None):
            os.environ[env_var] = old_env_var_value


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
        generated_config.setdefault('jupyterhub', {}).setdefault('hub', {}).setdefault('services', {})['hub-health'] = {
            'apiToken': hub_health_token,
            'admin': True

        }

        if 'docs_service' in self.spec['config'].keys() and self.spec['config']['docs_service']['enabled']:
            generated_config['jupyterhub']['hub']['services']['docs'] = {
                'url': f'http://docs-service.{self.spec["name"]}'
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
            generated_config['base-hub']['jupyterhub']['hub']['services']['dask-gateway'] = { 'apiToken': gateway_token }

        return generated_config

    def deploy(self, auth_provider, proxy_secret_key, skip_hub_health_test=False):
        """
        Deploy this hub
        """

        generated_values = self.get_generated_config(auth_provider, proxy_secret_key)

        with tempfile.NamedTemporaryFile(mode='w') as values_file, tempfile.NamedTemporaryFile(mode='w') as generated_values_file:
            json.dump(self.spec['config'], values_file)
            json.dump(generated_values, generated_values_file)
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
            # Can't test without deploying, since our service token isn't set by default
            subprocess.check_call(cmd)

            if not skip_hub_health_test:

                # FIXMEL: Clean this up
                if self.spec['template'] != 'base-hub':
                    service_api_token = generated_values["base-hub"]["jupyterhub"]["hub"]["services"]["hub-health"]["apiToken"]
                else:
                    service_api_token = generated_values["jupyterhub"]["hub"]["services"]["hub-health"]["apiToken"]

                domain = self.spec["domain"]
                if type(domain) == str:
                    hub_url = f'https://{domain}'

                else:
                    hub_url = f'https://{random.choice(domain)}'

                exit_code = pytest.main([
                    "-v", "deploy/tests",
                    "--hub-url", hub_url,
                    "--api-token", service_api_token,
                    "--hub-type", self.spec['template']
                ])
                if exit_code != 0:
                    raise(RuntimeError)
