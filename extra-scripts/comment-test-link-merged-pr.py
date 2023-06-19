"""
This script is used in our CI/CD pipeline to comment on a merged PR with a link
to the running GitHub Actions for monitoring of the deployment.

In order to comment on a Pull Request, we need its number. But because we do not
trigger this workflow in a Pull Request context, it is not readily available to us.
Instead, we extract the PR number from the message of the head commit in the push
event payload. In the case of a merged PR, this message will be of the form:
'Merge pull request #XXX from owner/branch'

The other piece of information we require is the URL of the running workflow
triggered by merging the Pull Request. We use the requests Python package to interact
with the GitHub REST API and pull a list of workflow runs for the repository.
We filter these runs by the following criteria: event that triggered the workflow,
branch the workflow run is associated with, workflows that were created within a
given date-time period, the head commit of the workflow run contains the relevant
Pull Request number, and the name of the *other* workflow that we want to provide
a link to.
"""
import os
import re
import sys
from datetime import datetime

import requests

# Get today's date in ISO format
today = datetime.now().strftime("%Y-%m-%d")

api_url = "https://api.github.com"

# === Get variables from the environment ===#
# COMMIT_MSG = ${{ github.event.head_commit.message }} in workflow file
commit_msg = os.environ.get("COMMIT_MSG", None)

# GITHUB_REPO = ${{ github.repository }} in workflow file
repo = os.environ.get("GITHUB_REPO", None)

# GITHUB_TOKEN = ${{ secrets.GITHUB_TOKEN }} in workflow file
token = os.environ.get("GITHUB_TOKEN", None)

branch = os.environ.get("BRANCH", None)
event = os.environ.get("EVENT", None)
workflow_name = os.environ.get("WORKFLOW_NAME", None)

# Check all env vars have been successfully set
required_vars = {
    "COMMIT_MSG": commit_msg,
    "GITHUB_REPO": repo,
    "GITHUB_TOKEN": token,
    "BRANCH": branch,
    "EVENT": event,
    "WORKFLOW_NAME": workflow_name,
}

for required_var in required_vars.keys():
    if required_vars[required_var] is None:
        raise ValueError(f"{required_var} env var must be set")

# Create headers to send with API requests
headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}",
}

# Use regex to extract the PR number from the commit message
match = re.search("(?<=#)[0-9]*", commit_msg)
pr_number = None if match is None else match.group(0)

# Check if 'Merge pull request' appears in the commit message. Continue execution
# if it DOES.
if "Merge pull request" not in commit_msg:
    sys.exit()

# List workflow runs for the repository. Filtered by event, branch, and
# creation time.
url = "/".join([api_url, "repos", repo, "actions", "runs"])
params = {
    "branch": branch,
    "event": event,
    "per_page": 100,
    # Reduce the number of results by only checking workflow runs that were
    # created today
    "created": f">={today}",
}
response = requests.get(url, headers=headers, params=params)
all_workflow_runs = response.json()["workflow_runs"]

# Detect if pagination is required and execute as needed
while ("Link" in response.headers.keys()) and (
    'rel="next"' in response.headers["Link"]
):
    next_url = re.search(r'(?<=<)([\S]*)(?=>; rel="next")', response.headers["Link"])
    response = requests.get(next_url.group(0), headers=headers)
    all_workflow_runs.extend(response.json()["workflow_runs"])

workflow_url = next(
    (
        workflow_run["html_url"]
        for workflow_run in all_workflow_runs
        if workflow_run["name"] == workflow_name
        and workflow_run["head_commit"]["message"] == commit_msg
    ),
    False,
)

if not workflow_url:
    sys.exit()

# Comment workflow URL to merged PR
url = "/".join([api_url, "repos", repo, "issues", pr_number, "comments"])
body = {
    "body": f":tada::tada::tada::tada:\n\nMonitor the deployment of the hubs here :point_right: {workflow_url}"
}
requests.post(url, headers=headers, json=body)
