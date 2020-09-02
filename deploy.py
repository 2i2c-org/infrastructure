import tempfile
from pathlib import Path
from ruamel.yaml import YAML
import subprocess
import hashlib
import hmac
import os

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ='safe', pure=True)

HERE = Path(__file__).parent
PROXY_SECRET_BASE = bytes.fromhex(os.environ['PROXY_SECRET_KEY'])

def load_hubs():
    with open(HERE / "hubs.yaml") as f:
        return yaml.load(f)

def get_proxy_secret(hub_name):
    return hmac.new(PROXY_SECRET_BASE, hub_name.encode(), hashlib.sha256).hexdigest()

def munge_values(hub_name, hub_values):
    # Set default hostname to be {hub_name}.alpha.2i2c.cloud
    ingress = hub_values.setdefault(
        'jupyterhub', {}
    ).setdefault(
        'ingress', {}
    )

    ingress['hosts'] = [f'{hub_name}.alpha.2i2c.cloud']

    ingress['tls'] = [
        {
            'secretName': f'{hub_name}-tls-secret',
            'hosts': ingress['hosts']
        }
    ]
    return hub_values

def deploy_hub(hub_name, hub_values):
    secret_values = {
        'jupyterhub':  {
            'proxy': {
                'secretToken': get_proxy_secret(hub_name)
            }
        }
    }
    # Modify hub values to set defaults
    hub_values = munge_values(hub_name, hub_values)

    with tempfile.NamedTemporaryFile() as values_file, tempfile.NamedTemporaryFile() as secret_values_file:
        yaml.dump(hub_values, values_file)
        yaml.dump(secret_values, secret_values_file)
        values_file.flush()
        secret_values_file.flush()
        cmd = [
            'helm', 'upgrade', '--install', '--create-namespace', '--wait',
            '--namespace', hub_name,
            hub_name, 'hub',
            '-f', values_file.name,
            '-f', secret_values_file.name
        ]
        print(f"Running {' '.join(cmd)}")
        subprocess.check_call(cmd)

hubs = load_hubs()

for hub, values in hubs['hubs'].items():
    deploy_hub(hub, values)