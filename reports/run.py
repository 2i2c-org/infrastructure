"""
Execute the reports in this directory with papermill & output them to a github repo
"""
import argparse
import os
import pathlib
import subprocess
from contextlib import contextmanager
from datetime import datetime
from tempfile import TemporaryDirectory

import papermill as pm

HERE = pathlib.Path(__file__).parent


@contextmanager
def auto_commit_git_repo(clone_url, message):
    with TemporaryDirectory() as d:
        subprocess.check_call(["git", "clone", clone_url, "--depth", "1", d])
        try:
            yield d
        finally:
            subprocess.check_call(["git", "add", "."], cwd=d)
            subprocess.check_call(["git", "commit", "-m", message], cwd=d)
            subprocess.check_call(["git", "push"], cwd=d)


reports = HERE.glob("*.ipynb")

with auto_commit_git_repo(
    "git@github.com:yuvipanda/2i2c-reports.git", "Test commits"
) as d:
    output_base = pathlib.Path(d)
    for report in reports:
        output_file = output_base / report.stem / datetime.now().isoformat()
        os.makedirs(output_file.parent, exist_ok=True)
        pm.execute_notebook(report, str(output_file) + ".ipynb")
