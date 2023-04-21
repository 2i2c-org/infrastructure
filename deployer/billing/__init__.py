from pathlib import PosixPath

from ruamel.yaml import YAML

yaml = YAML(typ="safe")

HERE = PosixPath(__file__).parent.parent
