import json
import os
from glob import glob

CONFIGURATOR_BASE_PATH = "/usr/local/etc/jupyterhub-configurator"

schema_files = sorted(glob(os.path.join(CONFIGURATOR_BASE_PATH, "*.schema.json")))

schemas = {}

for sf in schema_files:
    with open(sf) as f:
        schemas[sf] = json.load(f)

c.Configurator.schemas = schemas
