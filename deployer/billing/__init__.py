import re
from enum import Enum
from pathlib import PosixPath

import typer
from ruamel.yaml import YAML

yaml = YAML(typ="safe")

HERE = PosixPath(__file__).parent.parent


def month_validate(month_str: str):
    """
    Validate passed string matches YYYY-MM format.

    Returns values in YYYYMM format, which is used by bigquery
    """
    match = re.match(r"(\d\d\d\d)-(\d\d)", month_str)
    if not match:
        raise typer.BadParameter(
            f"{month_str} should be formatted as YYYY-MM (eg: 2023-02)"
        )
    return f"{match.group(1)}{match.group(2)}"


class CostTableOutputFormats(Enum):
    """
    Output formats supported by the generate-cost-table command
    """

    terminal = "terminal"
    google_sheet = "google-sheet"
