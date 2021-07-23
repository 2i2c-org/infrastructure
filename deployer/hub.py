from auth import KeyProvider
import hashlib
import hmac
import json
import os
import sys
import subprocess
import tempfile
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from textwrap import dedent
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from build import build_image
from utils import decrypt_file

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ='safe', pure=True)


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
        self.support = self.spec.get('support', {})

    def build_image(self):
        self.ensure_docker_credhelpers()
        build_image(self.spec['image_repo'])

    @contextmanager
    def auth(self):
        if self.spec['provider'] == 'gcp':
            yield from self.auth_gcp()
        elif self.spec['provider'] == 'kubeconfig':
            yield from self.auth_kubeconfig()
        else:
            raise ValueError(f'Provider {self.spec["provider"]} not supported')

    def ensure_docker_credhelpers(self):
        """
        Setup credHelper for current hub's image registry.

        Most image registries (like ECR, GCP Artifact registry, etc) use
        a docker credHelper (https://docs.docker.com/engine/reference/commandline/login/#credential-helpers)
        to authenticate, rather than a username & password. This requires an
        entry per registry in ~/.docker/config.json.

        This method ensures the appropriate credential helper is present
        """
        image_name = self.spec['image_repo']
        registry = image_name.split('/')[0]

        helper = None
        # pkg.dev is used by Google Cloud Artifact registry
        if registry.endswith('pkg.dev'):
            helper = 'gcloud'

        if helper is not None:
            dockercfg_path = os.path.expanduser('~/.docker/config.json')
            try:
                with open(dockercfg_path) as f:
                    config = json.load(f)
            except FileNotFoundError:
                config = {}

            helpers = config.get('credHelpers', {})
            if helpers.get(registry) != helper:
                helpers[registry] = helper
                config['credHelpers'] = helpers
                with open(dockercfg_path, 'w') as f:
                    json.dump(config, f, indent=4)

    def deploy_support(self):
        cert_manager_url = 'https://charts.jetstack.io'
        cert_manager_version = 'v1.3.1'

        print("Adding cert-manager chart repo...")
        subprocess.check_call([
            'helm', 'repo', 'add', 'jetstack', cert_manager_url,
        ])

        print("Updating cert-manager chart repo...")
        subprocess.check_call([
            'helm', 'repo', 'update',
        ])

        print("Provisioning cert-manager...")
        subprocess.check_call([
            'helm', 'upgrade', '--install', '--create-namespace',
            '--namespace', 'cert-manager',
            'cert-manager', 'jetstack/cert-manager',
            '--version', cert_manager_version,
            '--set', 'installCRDs=true'
        ])
        print("Done!")

        print("Support charts...")

        support_dir = Path(__file__).parent.parent / 'support'
        support_secrets_file = support_dir / 'secrets.yaml'

        with tempfile.NamedTemporaryFile(mode='w') as f, decrypt_file(support_secrets_file) as secret_file:
            yaml.dump(self.support.get('config', {}), f)
            f.flush()
            subprocess.check_call([
                'helm', 'upgrade', '--install', '--create-namespace',
                '--namespace', 'support',
                'support', str(support_dir),
                '-f', secret_file, '-f', f.name,
                '--wait'
            ])
        print("Done!")

    def auth_kubeconfig(self):
        """
        Context manager for authenticating with just a kubeconfig file

        For the duration of the contextmanager, we:
        1. Decrypt the file specified in kubeconfig.file with sops
        2. Set `KUBECONFIG` env var to our decrypted file path, so applications
           we call (primarily helm) will use that as config
        """
        config = self.spec['kubeconfig']
        config_path = config['file']

        with decrypt_file(config_path) as decrypted_key_path:
            # FIXME: Unset this after our yield
            os.environ['KUBECONFIG'] = decrypted_key_path
            yield

    def auth_gcp(self):
        config = self.spec['gcp']
        key_path = config['key']
        project = config['project']
        # If cluster is regional, it'll have a `region` key set.
        # Else, it'll just have a `zone` key set. Let's respect either.
        location = config.get('zone', config.get('region'))
        cluster = config['cluster']
        with tempfile.NamedTemporaryFile() as kubeconfig:
            orig_kubeconfig = os.environ.get('KUBECONFIG')
            try:
                os.environ['KUBECONFIG'] = kubeconfig.name
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
            finally:
                if orig_kubeconfig is not None:
                    os.environ['KUBECONFIG'] = orig_kubeconfig


class Hub:
    """
    A single, deployable JupyterHub
    """
    def __init__(self, cluster, spec):
        self.cluster = cluster
        self.spec = spec

    def get_generated_config(self, auth_provider: KeyProvider, secret_key):
        """
        Generate config automatically for each hub

        WARNING: MIGHT CONTAINS SECRET VALUES!
        """

        generated_config = {
            'jupyterhub': {
                'proxy': {
                    'https': {
                        'hosts': [self.spec['domain']]
                    }
                },
                'ingress': {
                    'hosts': [self.spec['domain']],
                    'tls': [
                        {
                            'secretName': 'https-auto-tls',
                            'hosts': [self.spec['domain']]
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
            # Auth0 sends users back to this URL after they authenticate
            callback_url = f"https://{self.spec['domain']}/hub/oauth_callback"
            # Users are redirected to this URL after they log out
            logout_url = f"https://{self.spec['domain']}"
            client = auth_provider.ensure_client(
                name=self.spec['auth0'].get('application_name', f"{self.cluster.spec['name']}-{self.spec['name']}"),
                callback_url=callback_url,
                logout_url=logout_url,
                connection_name=self.spec['auth0']['connection'],
                connection_config=self.spec['auth0'].get(self.spec['auth0']['connection'], {}),
            )
            # FIXME: We're hardcoding Auth0OAuthenticator here
            # We should *not*. We need dictionary merging in code, so
            # these can all exist fine.
            generated_config['jupyterhub']['hub']['config']['Auth0OAuthenticator'] = auth_provider.get_client_creds(client, self.spec['auth0']['connection'])

        return self.apply_hub_template_fixes(generated_config, secret_key)


    def unset_env_var(self, env_var, old_env_var_value):
        """
        If the old environment variable's value exists, replace the current one with the old one
        If the old environment variable's value does not exist, delete the current one
        """

        if env_var in os.environ:
            del os.environ[env_var]
        if (old_env_var_value is not None):
            os.environ[env_var] = old_env_var_value


    def apply_hub_template_fixes(self, generated_config, secret_key):
        """
        Modify generated_config based on what hub template we're using.

        Different hub templates require different pre-set config. For example,
        anything deriving from 'basehub' needs all config to be under a 'basehub'
        config. dask hubs require apiTokens, etc.

        Ideally, these would be done declaratively. Untile then, let's put all of
        them in this function.
        """
        hub_template = self.spec['template']

        # Generate a token for the hub health service
        hub_health_token = hmac.new(secret_key, 'health-'.encode() + self.spec['name'].encode(), hashlib.sha256).hexdigest()
        # Describe the hub health service
        generated_config.setdefault('jupyterhub', {}).setdefault('hub', {}).setdefault('services', {})['hub-health'] = {
            'apiToken': hub_health_token,
            'admin': True

        }

        docs_token = hmac.new(secret_key, f'docs-{self.spec["name"]}'.encode(), hashlib.sha256).hexdigest()
        if 'docs_service' in self.spec['config'].keys() and self.spec['config']['docs_service']['enabled']:
            generated_config['jupyterhub']['hub']['services']['docs'] = {
                'url': f'http://docs-service.{self.spec["name"]}',
                'apiToken': docs_token
            }


        # FIXME: Have a templates config somewhere? Maybe in Chart.yaml
        # FIXME: This is a hack. Fix it.
        if hub_template != 'basehub':
            generated_config = {
                'basehub': generated_config
            }

        # LOLSOB FIXME
        if hub_template == 'daskhub':
            gateway_token = hmac.new(secret_key, 'gateway-'.encode() + self.spec['name'].encode(), hashlib.sha256).hexdigest()
            generated_config['dask-gateway'] = {
                'gateway': {
                    'auth': {
                        'jupyterhub': { 'apiToken': gateway_token }
                    }
                }
            }
            generated_config['basehub']['jupyterhub']['hub']['services']['dask-gateway'] = { 'apiToken': gateway_token }

        return generated_config

    def deploy(self, auth_provider, secret_key, skip_hub_health_test=False):
        """
        Deploy this hub
        """

        generated_values = self.get_generated_config(auth_provider, secret_key)

        with tempfile.NamedTemporaryFile(mode='w') as values_file, tempfile.NamedTemporaryFile(mode='w') as generated_values_file:
            json.dump(self.spec['config'], values_file)
            json.dump(generated_values, generated_values_file)
            values_file.flush()
            generated_values_file.flush()

            cmd = [
                'helm', 'upgrade', '--install', '--create-namespace', '--wait',
                '--namespace', self.spec['name'],
                self.spec['name'], os.path.join('hub-templates', self.spec['template']),
                # Ordering matters here - config explicitly mentioned in clu should take
                # priority over our generated values. Based on how helm does overrides, this means
                # we should put the config from config/hubs last.
                '-f', generated_values_file.name,
                '-f', values_file.name,
            ]

            print(f"Running {' '.join(cmd)}")
            # Can't test without deploying, since our service token isn't set by default
            subprocess.check_call(cmd)

            if not skip_hub_health_test:

                # FIXMEL: Clean this up
                if self.spec['template'] != 'basehub':
                    service_api_token = generated_values["basehub"]["jupyterhub"]["hub"]["services"]["hub-health"]["apiToken"]
                else:
                    service_api_token = generated_values["jupyterhub"]["hub"]["services"]["hub-health"]["apiToken"]

                hub_url = f'https://{self.spec["domain"]}'

                # On failure, pytest prints out params to the test that failed.
                # This can contain sensitive info - so we hide stderr
                # FIXME: Try to be more granular here?
                print("Running hub health check...")
                with open(os.devnull, 'w') as dn, redirect_stderr(dn), redirect_stdout(dn):
                    exit_code = pytest.main([
                        "-q",
                        "deployer/tests",
                        "--hub-url", hub_url,
                        "--api-token", service_api_token,
                        "--hub-type", self.spec['template']
                    ])
                if exit_code != 0:
                    print("Health check failed!", file=sys.stderr)
                    sys.exit(exit_code)
                else:
                    print("Helath check succeeded!")
