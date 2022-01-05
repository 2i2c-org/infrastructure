"""
This script helps remind our team when it's time to merge a PR. It does these things:

- Grab a list of all open pull requests in our infrastructure repository.
- For any that have a PR approval, check how long ago that approval was.
- If the approval was longer than 24 hours ago, add it to a list of PRs we should merge
- Ping our #hub-development channel with a list of the PRs that are ready to merge
"""
from ghapi.all import GhApi
import pandas as pd

api = GhApi()

open_prs = api.pulls.list("2i2c-org", "infrastructure", state="open")

msg = ""
for pr in open_prs:
    print(f"Checking PR: {pr['title']} ({pr['html_url']})")
    reviews = api.pulls.list_reviews("2i2c-org", "infrastructure", pr["number"])
    for review in reviews:
        # Only care about reviews that caused approvals
        if review["state"] != "APPROVED":
            continue
        # Check whether we've had an approval for > 24 hours, and if so add to message list
        today = pd.to_datetime(datetime.today()).tz_localize("US/Pacific")
        review_time = pd.to_datetime(review["submitted_at"]).astimezone("US/Pacific")
        age = today - review_time
        hours_old = age.seconds // 60 // 60  # Convert to hours
        if hours_old > 24:
            msg += f"- [{pr['title']}]({pr['html_url']}) - {hours_old} hours old."
if msg:
    msg = (
        "**The following PRs are more than 24 hours old, have approval, and should be merged!**\n\n"
        + msg
    )
    # Print to output in a way that will store as an environment variable
    print("Found PRs with old approvals, sending Slack message")
    print(f"::set-output name=PRS_MESSAGE::{msg}")
    print(f"::set-output name=DO_SEND_MESSAGE::TRUE")
else:
    print("No PRs with old approvals found, not sending Slack message")
    print(f"::set-output name=DO_SEND_MESSAGE::FALSE")
