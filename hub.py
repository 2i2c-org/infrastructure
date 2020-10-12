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

    def get_generated_config(self):
        """
        Generate config automatically for each hub

        Some config should be automatically set for all hubs based on
        spec in hubs.yaml. We generate them here.

        Shouldn't have anything secret here.
        """

        return {
            'jupyterhub': {
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
                    'storage': {
                        'static': {
                            'subPath': 'homes/' + self.spec['name'] + '/{username}'
                        }
                    }
                },
                'hub': {
                    'extraaEnv': {
                        'OAUTH_CALLBACK_URL': f'https://{self.spec["domain"]}/hub/oauth_callback'
                    }
                }
            }
        }

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

        generated_values = self.get_generated_config()
        with tempfile.NamedTemporaryFile() as values_file, tempfile.NamedTemporaryFile() as generated_values_file, tempfile.NamedTemporaryFile() as secret_values_file:
            yaml.dump(self.spec['config'], values_file)
            yaml.dump(generated_values, generated_values_file)
            yaml.dump(secret_values, secret_values_file)
            values_file.flush()
            generated_values_file.flush()
            secret_values_file.flush()
            cmd = [
                'helm', 'upgrade', '--install', '--create-namespace', '--wait',
                '--namespace', self.spec['name'],
                self.spec['name'], 'hub',
                '-f', values_file.name,
                '-f', generated_values_file.name,
                '-f', secret_values_file.name
            ]
            print(f"Running {' '.join(cmd)}")
            subprocess.check_call(cmd)

