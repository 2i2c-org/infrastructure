"""
During our CI/CD deployment pipeline, we create a deployment plan that describes
which hubs will be upgraded as a result of a merge. This script is run in CI/CD
to download the markdown content of the deployment plan from a GitHub Actions
workflow artifact and then post it as a comment on the PR that generated the plan.
"""
import io
import os
import re
import sys
import zipfile

import requests

# === Setup variables ===#
# GITHUB_REPOSITORY = ${{ github.repository }} in workflow file
repo = os.environ.get("GITHUB_REPOSITORY", None)
if repo is None:
    raise ValueError("GITHUB_REPOSITORY env var must be set")

# RUN_ID = ${{ github.event.workflow_run.id }} in workflow file
run_id = os.environ.get("RUN_ID", None)
if run_id is None:
    raise ValueError("RUN_ID env var must be set")

# GITHUB_TOKEN = ${{ secrets.GITHUB_TOKEN }} in workflow file
token = os.environ.get("GITHUB_TOKEN", None)
if token is None:
    raise ValueError("GITHUB_TOKEN env var must be set")

api_url = "https://api.github.com"

# Construct headers to send with requests
headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}",
}

# List all artifacts for the workflow run
url = "/".join([api_url, "repos", repo, "actions", "runs", run_id, "artifacts"])
params = {"per_page": 100}
response = requests.get(url, headers=headers, params=params)
all_artifacts = response.json()["artifacts"]

# If "Link" is present in the response headers, that means that the results are
# paginated and we need to loop through them to collect all the results.
# It is unlikely that we will have more than 100 artifact results for a single
# worflow ID however.
while ("Link" in response.headers.keys()) and (
    'rel="next"' in response.headers["Link"]
):
    next_url = re.search(r'(?<=<)([\S]*)(?=>; rel="next")', response.headers["Link"])
    response = requests.get(next_url.group(0), headers=headers)
    all_artifacts.extend(response.json()["artifacts"])

# Filter for the artifact with the name we want: 'pr'
artifact_id = next(
    (artifact["id"] for artifact in all_artifacts if artifact["name"] == "pr"),
    None,
)

if artifact_id is None:
    print(f"No artifact found called 'pr' for workflow run: {run_id}")
    sys.exit()

# Download the artifact
url = "/".join(
    [api_url, "repos", repo, "actions", "artifacts", str(artifact_id), "zip"]
)
response = requests.get(url, headers=headers, stream=True)

# Extract the zip archive
with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
    zip_ref.extractall(os.getcwd())

# Read in Pull Request number
with open("pr-number.txt") as f:
    pr_number = f.read().strip("\n")

# Read in comment body
with open("comment-body.txt") as f:
    comment_body = f.read().strip("\n")
body = {"body": comment_body}

# List all comments on the PR
url = "/".join([api_url, "repos", repo, "issues", pr_number, "comments"])
params = {"per_page": 100}
response = requests.get(url, headers=headers, params=params)
issue_comments = response.json()

# If "Link" is present in the response headers, that means that the results are
# paginated and we need to loop through them to collect all the results.
while ("Link" in response.headers.keys()) and (
    'rel="next"' in response.headers["Link"]
):
    next_url = re.search(r'(?<=<)([\S]*)(?=>; rel="next")', response.headers["Link"])
    response = requests.get(next_url.group(0), headers=headers)
    issue_comments.extend(response.json())

# Otherwise, if no `issue_comments`, this will be undefined
comment_id = None

# Find if a deployment-plan comment has been previously posted
comment_id = next(
    (
        comment["id"]
        for comment in issue_comments
        if comment["user"]["login"] == "github-actions[bot]"
        and "<!-- deployment-plan -->" in comment["body"]
    ),
    None,
)

if comment_id is not None:
    # Comment exists - update it
    url = "/".join([api_url, "repos", repo, "issues", "comments", str(comment_id)])
    requests.patch(url, headers=headers, json=body)
else:
    # Comment doesn't exist - create a new one
    url = "/".join([api_url, "repos", repo, "issues", pr_number, "comments"])
    requests.post(url, headers=headers, json=body)
