"""
Execute the reports in this directory with papermill & output them to a github repo
"""
import os
import pathlib
import subprocess
from contextlib import contextmanager
from datetime import datetime, timezone
from tempfile import TemporaryDirectory

import papermill as pm
import typer

from .cli_app import app

REPO_ROOT = pathlib.Path(__file__).parent.parent


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


@app.command()
def publish_reports(
    target_git_repo: str = typer.Option("git@github.com:yuvipanda/2i2c-reports.git"),
    commit_message: str = typer.Option(
        "Automatically commiting and publishing generated reports"
    ),
):
    # All .ipynb files under reports/ will be considered as a report
    reports = (REPO_ROOT / "reports").glob("*.ipynb")

    report_date = datetime.now(timezone.utc)

    with auto_commit_git_repo(target_git_repo, commit_message) as d:
        output_base = pathlib.Path(d)
        for report in reports:
            output_file = (
                output_base / report.stem / report_date.strftime("%Y/%m/%d-%Hh%Mm%Ss%Z")
            ).with_suffix(".ipynb")
            os.makedirs(output_file.parent, exist_ok=True)
            pm.execute_notebook(report, str(output_file))
