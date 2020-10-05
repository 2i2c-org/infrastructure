from copy import deepcopy
import hashlib
import subprocess
import hmac
import tempfile
from ruamel.yaml import YAML
from build import last_modified_commit

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ='safe', pure=True)

class Hub:
    """
    A single, deployable JupyterHub
    """
    def __init__(self, spec, auth_provider, proxy_secret_key):
        self.spec = spec
        self.auth_provider = auth_provider
        self.proxy_secret_key = proxy_secret_key

    def _setup_ingress(self, jupyterhub):
        # Setup automatic ingress + TLS for given domain
        # We don't allow customization of this per-hub
        jupyterhub['ingress'] = {
            'hosts': [self.spec['domain']],
            'tls': [
                {
                    'secretName': f'https-auto-tls',
                    'hosts': [self.spec['domain']]
                }
            ]
        }

        return jupyterhub

    def _setup_auth0(self, jupyterhub):
        hub = jupyterhub.setdefault('hub', {})
        extraEnv = hub.setdefault('extraEnv', {})
        extraEnv['OAUTH_CALLBACK_URL'] = f'https://{self.spec["domain"]}/hub/oauth_callback'

        return jupyterhub

    def _setup_image(self, jupyterhub):
        singleuser = jupyterhub.setdefault('singleuser', {})
        image = singleuser.setdefault('image', {})
        # FIXME: parameterize this better?
        image['tag'] = last_modified_commit("images/user/")

        return jupyterhub

    @property
    def full_config(self):
        config = deepcopy(self.spec['config'])

        # config should always have a 'jupyterhub' section
        jupyterhub = config.setdefault('jupyterhub', {})
        jupyterhub = self._setup_ingress(jupyterhub)
        jupyterhub = self._setup_auth0(jupyterhub)
        jupyterhub = self._setup_image(jupyterhub)

        return config

    @property
    def proxy_secret(self):
        return hmac.new(self.proxy_secret_key, self.spec['name'].encode(), hashlib.sha256).hexdigest()

    def deploy(self):
        client = self.auth_provider.ensure_client(
            self.spec['name'],
            self.spec['domain'],
            self.spec['auth0']['connection']
        )

        secret_values = {
            'jupyterhub':  {
                'proxy': {
                    'secretToken': self.proxy_secret
                },
                'auth': self.auth_provider.get_client_creds(client, self.spec['auth0']['connection'])
            }
        }

        with tempfile.NamedTemporaryFile() as values_file, tempfile.NamedTemporaryFile() as secret_values_file:
            yaml.dump(self.full_config, values_file)
            yaml.dump(secret_values, secret_values_file)
            values_file.flush()
            secret_values_file.flush()
            cmd = [
                'helm', 'upgrade', '--install', '--create-namespace', '--wait',
                '--namespace', self.spec['name'],
                self.spec['name'], 'hub',
                '-f', values_file.name,
                '-f', secret_values_file.name
            ]
            print(f"Running {' '.join(cmd)}")
            subprocess.check_call(cmd)

