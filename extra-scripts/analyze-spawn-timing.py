"""
Reconstruct user server spawn timelines from the Kubernetes Events we ship to
CloudWatch Logs through Fluent Bit.

The Kubernetes events can tell us per pod when the autoscaler
asked for a node, when the pod started, and how long each image pull took etc.
This script turns that stream of individual events back into one row per spawn,
so we can ask where the time actually went and how that changes over time.

Usage:

    # Analyze events directly from CloudWatch (needs AWS credentials for the cluster account)
    python analyze-spawn-timing.py --cluster maap --hours 24 --out spawns.csv

    # Filtering by namespace. (note: the filtering happens server-side on CloudWatch)
    python analyze-spawn-timing.py --cluster maap --namespace prod --hours 72

    # Or from a file of events as JSON lines. This is handy for iterating
    # without re-querying:
    #
    #   aws logs filter-log-events \
    #     --log-group-name /2i2c/maap/k8s-events \
    #     --start-time $(( ($(date +%s) - 86400) * 1000 )) \
    #     --region us-west-2 --output json \
    #     --filter-pattern '{ $.involvedObject.name = "jupyter-*" }' \
    #     | jq -c '.events[].message | fromjson' > events.jsonl
    #
    python analyze-spawn-timing.py --from-file events.jsonl --out spawns.csv

Add `--per-image` to write a second row-per-image-pull CSV, which is what we
want to answer "which images are slow to pull" as opposed to "which spawns are slow".

The tool prints a distribution of where boot time goes. The components are:

    total: the total boot time
    node_wait: time waiting for the node to be ready
    image_pull: time pulling the Docker image
    other: everything else


By default that is one row per component (total, node_wait, image_pull, other) with

    n: number of spawns
    min: minimum boot time
    mean: mean boot time
    p50: median boot time
    p95: 95th percentile boot time
    p99: 99th percentile boot time
    max: maximum boot time

Here are some examples of how to shape the output:

    # Percentiles of total and each component
    python analyze-spawn-timing.py --from-file events.jsonl

    # Node-scaling time by node type, at custom percentiles
    python analyze-spawn-timing.py --cluster maap \
        --metric node_wait --group-by instance_type --percentiles 50,95,99

    # Image-pull time per image written as CSV
    python analyze-spawn-timing.py --cluster maap \
        --group-by image --stats-out image-stats.csv

    # Boot time for one node type only (--where keeps matching rows)
    python analyze-spawn-timing.py --cluster maap \
        --metric total --where instance_type=r5.xlarge

    # Trend of node-scale-up wait over the last 30 days
    python analyze-spawn-timing.py --cluster maap --hours 720 \
        --metric node_wait --group-by day

    # The five slowest and five fastest boots, and what they had in common
    python analyze-spawn-timing.py --from-file events.jsonl \
        --metric total --extremes 5

`--metric` takes a comma-separated list (total, node_wait, image_pull, other,
pull); `--group-by` takes one of instance_type, hub, node, namespace,
cold_start, scale_up, image, cached, day, week. Grouping by image or cached
summarises the per-pull durations; the rest summarise per-spawn components.
Grouping by day or week reads as a trend (oldest first) and pairs well with a
wide `--hours`. `--where key=value` (repeatable) narrows to matching rows first,
e.g. a single node type or image; a grouped table also shows each group's share
of rows.

`--extremes N` prints, under each table, the N slowest and N fastest rows behind
it, with the fields that explain them: node type, cold start, where the time
went, the slowest image. That is the view for "what do the extremes have in
common", as opposed to "what is typical". It respects `--where` too, so we can
ask for the extremes of one node type.

`total_s` measures to the first start of each container, so a pod that restarts
something later is not counted as a slow boot; `n_restarts` records that it
happened. `--max-total SECONDS` remains as a backstop for anything else that
comes out implausible: it leaves those spawns out of the stats and the extremes
and prints what it left out. The CSVs written by `--out` and `--per-image` still
hold every spawn.

Wide windows are slow because CloudWatch scans the whole log group to find our
events; `--concurrency` fetches that many time shards in parallel, with a
progress line so a long scan doesn't look hung. Raise it for a 30-day pull
(e.g. `--hours 720 --concurrency 8`), lower it if we hit throttling.
"""

import csv
import json
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import click

# Only look at user server pods of the pattern `jupyter-<username>`.
USER_POD_RE = re.compile(r"^jupyter-")

# What we can take a distribution of, and which of the two categories it belongs to.
METRICS = {
    "total": ("spawn", "total_s"),
    "node_wait": ("spawn", "node_wait_s"),
    "image_pull": ("spawn", "image_pull_s"),
    "other": ("spawn", "other_s"),
    "pull": ("pull", "duration_s"),
}
# Dimensions we can break a metric down by. "both" dimensions exist on spawn
# and pull rows alike, so they pair with either grain; the rest are grain-bound.
# `day`/`week` are time buckets derived from the row's timestamp (see
# time_bucket), so grouping by them reads as a trend.
GROUP_DIMS = {
    "instance_type": ("both", "instance_type"),
    "hub": ("spawn", "hub"),
    "node": ("spawn", "node"),
    "namespace": ("spawn", "namespace"),
    "cold_start": ("spawn", "cold_start"),
    "scale_up": ("spawn", "scale_up"),
    "image": ("pull", "image"),
    "cached": ("pull", "cached"),
    "day": ("both", "_day"),
    "week": ("both", "_week"),
}
# What an --extremes listing shows for one row, per grain: the fields that
# explain why the row landed at that end of the distribution.
EXTREME_COLS = {
    "spawn": [
        "started_at",
        "hub",
        "instance_type",
        "cold_start",
        "total_s",
        "node_wait_s",
        "image_pull_s",
        "other_s",
        "n_restarts",
        "n_cold_pulls",
        "slowest_image",
    ],
    "pull": [
        "started_at",
        "instance_type",
        "image",
        "duration_s",
        "size_bytes",
        "cached",
    ],
}

# The group-by dimensions that are time buckets; grouping by these sorts
# chronologically instead of slowest-first, so the output reads as a trend.
TIME_DIMS = ("day", "week")
# Dimensions we can also filter rows by with --where. Time buckets are excluded
# (filter with --hours instead); the rest are plain row values.
WHERE_DIMS = {k: v for k, v in GROUP_DIMS.items() if k not in TIME_DIMS}

# Go duration strings, as used in kubelet's "pulled in 1m40.153s" messages.
_GO_DURATION_UNITS = {
    "ns": 1e-9,
    "us": 1e-6,
    "µs": 1e-6,
    "ms": 1e-3,
    "s": 1.0,
    "m": 60.0,
    "h": 3600.0,
}
_GO_DURATION_PART_RE = re.compile(r"(\d+(?:\.\d+)?)(ns|us|µs|ms|s|m|h)")

# "Successfully pulled image "repo/name:tag" in 1m40.153s (1m40.153s including
#  waiting). Image size: 2133483009 bytes."
_PULLED_RE = re.compile(
    r'Successfully pulled image "(?P<image>[^"]+)" in (?P<duration>[0-9smhun.µ]+)'
    r"(?: \((?P<including_waiting>[0-9smhun.µ]+) including waiting\))?"
    r"(?:.*?Image size: (?P<size>\d+) bytes)?"
)
# "Container image "repo/name:tag" already present on machine"
_CACHED_RE = re.compile(
    r'Container image "(?P<image>[^"]+)" already present on machine'
)
# "Started container notebook"
_STARTED_RE = re.compile(r"^Started container (?P<container>\S+)")
# "Successfully assigned staging/jupyter-foo to ip-192-168-19-200.us-west-2..."
_SCHEDULED_RE = re.compile(r"Successfully assigned \S+ to (?P<node>\S+)")
# "pod triggered scale-up: [{eks-nb-staging-r5-xlarge-d-86ce48cb-... 0->1 (max: 100)}]"
_SCALE_UP_RE = re.compile(
    r"triggered scale-up: \[\{(?P<nodegroup>\S+) (?P<from>\d+)->(?P<to>\d+)"
)
# Trailing EKS-generated id on an ASG name, e.g. "-86ce48cb-82a6-e798-c3b0-0dc0ce305be9"
_ASG_SUFFIX_RE = re.compile(r"-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$")


def parse_go_duration(text):
    """Turn a Go duration such as '1m40.153s' or '449ms' into seconds."""
    if not text:
        return None
    parts = _GO_DURATION_PART_RE.findall(text)
    if not parts:
        return None
    return sum(float(value) * _GO_DURATION_UNITS[unit] for value, unit in parts)


def parse_nodegroup(nodegroup):
    """Pull the hub and EC2 instance type out of an autoscaling group name.

    eksctl names our user nodegroups `nb-<hub>-<instance type>-<generation>`,
    with dots in the instance type replaced by dashes (see
    eksctl/libsonnet/cluster.jsonnet), then EKS prefixes `eks-` and appends an
    id. So `eks-nb-staging-r5-xlarge-d-86ce48cb-...` describes an r5.xlarge
    running the staging hub's user pods.

    Returns (hub, instance_type), either of which may be None if the name
    doesn't look like one of ours - a nodegroup created by hand, say.
    """
    if not nodegroup:
        return None, None
    name = _ASG_SUFFIX_RE.sub("", nodegroup)
    name = name.removeprefix("eks-")
    if not name.startswith("nb-"):
        # Not a user nodegroup (core nodes, or something we didn't create).
        return None, None
    tokens = name.removeprefix("nb-").split("-")
    # Last three tokens are <family>-<size>-<generation>; everything before
    # them is the hub name, which may itself contain dashes.
    if len(tokens) < 4:
        return None, None
    hub = "-".join(tokens[:-3])
    instance_type = f"{tokens[-3]}.{tokens[-2]}"
    return hub or None, instance_type


def event_time(event):
    """When an event first happened, as an aware datetime.

    Kubernetes aggregates repeats of the same event into one object: `count`
    goes up and `lastTimestamp` moves to the newest occurrence, while
    `firstTimestamp` stays put. So `lastTimestamp` on an aggregated event is the
    time of the *last* repeat, which is not what any of our measurements want -
    a container that restarts hours later would move its "Started" event to the
    restart and read as an hours-long boot.

    Taking the first occurrence also makes us deterministic. We see the same
    event object shipped more than once with a different `count` each time, and
    those copies disagree about `lastTimestamp` but agree about
    `firstTimestamp`, so which copy we happened to keep no longer changes the
    answer. `eventTime` comes first because it is a single occurrence with
    microseconds; for a series event it is also the first observation.
    """
    for key in ("eventTime", "firstTimestamp", "lastTimestamp"):
        value = event.get(key)
        if value:
            # Kubernetes uses RFC3339 with a trailing Z, and eventTime carries
            # microseconds.
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                continue
    creation = event.get("metadata", {}).get("creationTimestamp")
    if creation:
        try:
            return datetime.fromisoformat(creation.replace("Z", "+00:00"))
        except ValueError:
            pass
    return None


def dedup_key(event):
    """Identify one Event object, so a re-delivered copy is only counted once.

    We have seen every event arrive twice, which doubles `image_pull_s` (a sum)
    while leaving `total_s` and `node_wait_s` (a max and an assignment) alone,
    so spawns come out with a large negative `other_s`.

    Kubernetes gives each Event its own metadata.uid, and it aggregates repeats
    of the same event into one object rather than emitting a new one. Two
    containers pulling the same image are two separate Events with separate
    uids, so this drops copies without dropping real pulls.
    """
    uid = event.get("metadata", {}).get("uid")
    if uid:
        return uid
    # No metadata.uid stored: fall back to the content. The message carries the
    # measured duration and the timestamp carries microseconds, so two real
    # events colliding here is unlikely.
    involved = event.get("involvedObject", {})
    return (
        involved.get("uid"),
        involved.get("name"),
        event.get("reason"),
        event.get("message"),
        event.get("eventTime") or event.get("lastTimestamp"),
    )


def spawn_key(event):
    """Group events belonging to one pod instance.

    involvedObject.uid is unique per pod, so it separates a user's spawn today
    from the same user's spawn yesterday. Without it we'd have to guess based
    on time gaps, so fall back to that only if uid is missing.
    """
    involved = event.get("involvedObject", {})
    if involved.get("uid"):
        return involved["uid"]
    return f"{involved.get('namespace')}/{involved.get('name')}"


def summarise_spawn(events):
    """Build one summary row from all the events for a single pod."""
    events = sorted(events, key=lambda e: e["_ts"])
    involved = events[0].get("involvedObject", {})

    first_ts = events[0]["_ts"]
    scheduled_at = None
    node = None
    hub = None
    instance_type = None
    scale_up_requested = False
    unschedulable = False
    # When each container first started. A pod that restarts a container hours
    # later starts it again, and that later start says nothing about how long
    # the pod took to boot, so only the first one per container counts.
    container_started_at = {}
    restarts = 0
    pulls = []

    for event in events:
        reason = event.get("reason")
        message = event.get("message") or ""
        ts = event["_ts"]

        if reason == "FailedScheduling":
            unschedulable = True
        elif reason == "TriggeredScaleUp":
            scale_up_requested = True
            match = _SCALE_UP_RE.search(message)
            if match:
                hub, instance_type = parse_nodegroup(match.group("nodegroup"))
        elif reason == "Scheduled":
            scheduled_at = ts
            match = _SCHEDULED_RE.search(message)
            if match:
                node = match.group("node")
        elif reason == "Pulled":
            match = _PULLED_RE.search(message)
            if match:
                duration = parse_go_duration(match.group("duration"))
                size = match.group("size")
                pulls.append(
                    {
                        "image": match.group("image"),
                        "duration_s": duration,
                        "size_bytes": int(size) if size else None,
                        "cached": False,
                        # The event fires when the pull finishes, so we can
                        # recover the start even if we missed the Pulling event.
                        "finished_at": ts,
                        "started_at": (
                            ts - timedelta(seconds=duration)
                            if duration is not None
                            else None
                        ),
                    }
                )
            else:
                match = _CACHED_RE.search(message)
                if match:
                    pulls.append(
                        {
                            "image": match.group("image"),
                            "duration_s": 0.0,
                            "size_bytes": None,
                            "cached": True,
                            "finished_at": ts,
                            "started_at": ts,
                        }
                    )
        elif reason == "Started":
            match = _STARTED_RE.search(message)
            container = match.group("container") if match else message
            if container in container_started_at:
                restarts += 1
            else:
                container_started_at[container] = ts

    # The node type isn't known until we've seen the scale-up event, which may
    # come after the Pulled events, so stamp it on now that the loop is done.
    for pull in pulls:
        pull["instance_type"] = instance_type

    pull_total = sum(p["duration_s"] or 0.0 for p in pulls)
    cold_pulls = [p for p in pulls if not p["cached"]]

    # Time from the pod first being noticed to it being placed on a node. When
    # the cluster had to scale up, this is dominated by waiting for the EC2
    # instance to boot and join.
    node_wait = (scheduled_at - first_ts).total_seconds() if scheduled_at else None
    # The pod is up once its slowest container has started for the first time.
    booted_at = max(container_started_at.values()) if container_started_at else None
    total = (booted_at - first_ts).total_seconds() if booted_at else None
    # Whatever is left once we account for waiting on a node and pulling
    # images: container creation, init containers doing actual work, etc.
    other = None
    if total is not None and node_wait is not None:
        other = total - node_wait - pull_total

    return {
        "pod": involved.get("name"),
        "namespace": involved.get("namespace"),
        "started_at": first_ts.isoformat() if first_ts else None,
        "total_s": round(total, 2) if total is not None else None,
        "node_wait_s": round(node_wait, 2) if node_wait is not None else None,
        "image_pull_s": round(pull_total, 2),
        "other_s": round(other, 2) if other is not None else None,
        "cold_start": scale_up_requested or unschedulable,
        "scale_up": scale_up_requested,
        "instance_type": instance_type,
        "hub": hub or involved.get("namespace"),
        "node": node,
        "n_images": len(pulls),
        # Containers started again after their first start. Non-zero means the
        # pod restarted something after booting, which is worth knowing when a
        # row looks slow - though it no longer inflates total_s.
        "n_restarts": restarts,
        "n_cold_pulls": len(cold_pulls),
        "cold_pull_bytes": sum(p["size_bytes"] or 0 for p in cold_pulls) or None,
        "slowest_image": (
            max(cold_pulls, key=lambda p: p["duration_s"] or 0)["image"]
            if cold_pulls
            else None
        ),
        "_pulls": pulls,
    }


def load_events_from_file(path):
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def cloudwatch_filter_pattern(namespace):
    """A CloudWatch filter pattern matching only the events we keep.

    The log group holds every Event in the cluster - kube-system, support, node
    scaling, both hub namespaces - and user server spawns are a small part of
    that. Selecting server-side means CloudWatch does the discarding, rather
    than us paging the whole group over the network to drop most of it.

    Returns None if there is nothing to narrow by.
    """
    terms = ['$.involvedObject.name = "jupyter-*"']
    if namespace:
        terms.append(f'$.involvedObject.namespace = "{namespace}"')
    return "{ " + " && ".join(terms) + " }"


def shard_bounds(start_ms, end_ms, k):
    """Split [start_ms, end_ms) into k contiguous, non-overlapping windows.

    CloudWatch's startTime is inclusive and endTime exclusive, so contiguous
    edges give an exact partition of the range - no duplicated or dropped
    events at the seams.
    """
    step = (end_ms - start_ms) / k
    edges = [int(start_ms + i * step) for i in range(k)] + [end_ms]
    return list(zip(edges, edges[1:]))


def _print_fetch_progress(counters, total_shards, started, live, final=False):
    """A one-line fetch status on stderr, so a long scan doesn't look hung."""
    import time

    elapsed = time.monotonic() - started
    msg = (
        f"fetching {counters['shards_done']}/{total_shards} shards  "
        f"{counters['events']:,} events  {elapsed:.0f}s"
    )
    if final:
        # Land the cursor on a fresh line, clearing any live remnant.
        print(f"\r{msg}{' ' * 8}", file=sys.stderr)
    elif live:
        print(f"\r{msg}", end="", file=sys.stderr, flush=True)
    else:
        # Not a TTY: a plain line (called only on shard completion) so piped
        # runs still get periodic, non-spammy updates.
        print(msg, file=sys.stderr)


def load_events_from_cloudwatch(
    log_group, region, hours, filter_pattern=None, concurrency=4, progress=True
):
    """Yield events from CloudWatch, fetching time shards in parallel.

    The filter pattern makes CloudWatch scan the whole log group server-side, so
    a wide window is slow to first byte. Splitting the window into `concurrency`
    shards fetched on separate threads scans smaller ranges in parallel, and a
    progress line reports as each shard's pages arrive.
    """
    import queue
    import threading
    import time

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_ms = int(
        (datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp() * 1000
    )
    concurrency = max(1, concurrency)
    bounds = shard_bounds(start_ms, now_ms, concurrency)

    results = queue.Queue(maxsize=1000)
    sentinel = object()
    counters = {"events": 0, "shards_done": 0}
    lock = threading.Lock()

    def worker(lo, hi):
        # A client per thread: boto3 clients aren't guaranteed thread-safe to
        # share, but one-per-thread is cheap and safe.
        import boto3

        client = boto3.client("logs", region_name=region)
        kwargs = {"logGroupName": log_group, "startTime": lo, "endTime": hi}
        if filter_pattern:
            kwargs["filterPattern"] = filter_pattern
        paginator = client.get_paginator("filter_log_events")
        for page in paginator.paginate(**kwargs):
            batch = []
            for entry in page.get("events", []):
                try:
                    batch.append(json.loads(entry["message"]))
                except json.JSONDecodeError:
                    continue
            if batch:
                with lock:
                    counters["events"] += len(batch)
                results.put(batch)
        with lock:
            counters["shards_done"] += 1
        results.put(sentinel)

    threads = [
        threading.Thread(target=worker, args=(lo, hi), daemon=True) for lo, hi in bounds
    ]
    for t in threads:
        t.start()

    live = progress and sys.stderr.isatty()
    started = time.monotonic()
    last_print = 0.0
    finished = 0
    while finished < concurrency:
        item = results.get()
        if item is sentinel:
            finished += 1
            if progress:
                _print_fetch_progress(counters, concurrency, started, live)
            continue
        yield from item
        if live and (time.monotonic() - last_print) > 0.25:
            _print_fetch_progress(counters, concurrency, started, live)
            last_print = time.monotonic()
    if progress:
        _print_fetch_progress(counters, concurrency, started, live, final=True)


def percentile(sorted_xs, p):
    """The p-th percentile (0-100) of an already-sorted, non-empty list.

    Linear interpolation between the two nearest ranks, matching numpy's
    default. With a single value there is nothing to interpolate between, so
    return it.
    """
    if len(sorted_xs) == 1:
        return sorted_xs[0]
    rank = (p / 100) * (len(sorted_xs) - 1)
    low = int(rank)
    high = min(low + 1, len(sorted_xs) - 1)
    return sorted_xs[low] + (sorted_xs[high] - sorted_xs[low]) * (rank - low)


def summarize(values, percentiles):
    """n, min, mean, the requested percentiles, and max of `values`.

    Drops None (a component we couldn't measure). Returns None if nothing is
    left, so a caller can skip an empty metric or group.
    """
    xs = sorted(v for v in values if v is not None)
    if not xs:
        return None
    row = {"n": len(xs), "min": round(xs[0], 2), "mean": round(statistics.fmean(xs), 2)}
    for p in percentiles:
        row[f"p{p:g}"] = round(percentile(xs, p), 2)
    row["max"] = round(xs[-1], 2)
    return row


def select_rows(spawns, grain, where=()):
    """The rows a metric lives on, narrowed by any --where filters.

    One row per spawn, or one per image pull. `where` is a list of (key, value)
    equality filters; the stats and the extremes both go through here so they
    always describe the same population.
    """
    if grain == "pull":
        rows = [pull for spawn in spawns for pull in spawn["_pulls"]]
    else:
        rows = spawns
    if where:
        rows = [r for r in rows if all(str(r.get(k)) == v for k, v in where)]
    return rows


def short_image(ref):
    """An image reference short enough for a table cell.

    Ours run to about a hundred characters, which makes an extremes table
    unreadable. Keep the last two path segments and the tag - enough to tell
    them apart - and leave the full reference to the CSVs.
    """
    if not ref:
        return ref
    parts = ref.split("/")
    return "/".join(parts[-2:]) if len(parts) > 2 else ref


def time_bucket(row, unit):
    """The day or ISO week a row falls in, from its timestamp.

    Spawn rows carry `started_at` as an ISO string; pull rows carry
    `finished_at` (and sometimes `started_at`) as a datetime. Returns None if no
    usable timestamp is present, so such rows sort to the end of a trend.
    """
    ts = row.get("started_at") or row.get("finished_at")
    if ts is None:
        return None
    if isinstance(ts, str):
        try:
            ts = datetime.fromisoformat(ts)
        except ValueError:
            return None
    return ts.strftime("%G-W%V") if unit == "week" else ts.strftime("%Y-%m-%d")


def compute_stats(spawns, metric_names, group_by, percentiles, where=()):
    """One summary record per metric (and per group, if grouping).

    Each record is {"metric", "group", n, min, mean, p..., max}, plus "share"
    (percent of the metric's rows) when grouping. Rows can be narrowed first
    with `where`, a list of (key, value) equality filters. Groups come out
    slowest-first by median, except the `day`/`week` time buckets, which come
    out oldest-first so they read as a trend.
    """
    records = []
    for name in metric_names:
        grain, metric_key = METRICS[name]
        rows = select_rows(spawns, grain, where)
        if group_by:
            is_time = group_by in TIME_DIMS
            dim_key = GROUP_DIMS[group_by][1]
            buckets = defaultdict(list)
            for row in rows:
                key = time_bucket(row, group_by) if is_time else row.get(dim_key)
                buckets[key].append(row.get(metric_key))
            summaries = []
            for group_value, values in buckets.items():
                summary = summarize(values, percentiles)
                if summary:
                    summaries.append((group_value, summary))
            if is_time:
                # Oldest first; a None bucket (no timestamp) sinks to the end.
                summaries.sort(key=lambda gs: gs[0] or "￿")
            else:
                summaries.sort(
                    key=lambda gs: gs[1].get("p50", gs[1]["mean"]), reverse=True
                )
            total_n = sum(s["n"] for _, s in summaries)
            for group_value, summary in summaries:
                share = round(100 * summary["n"] / total_n, 1) if total_n else 0.0
                records.append(
                    {"metric": name, "group": group_value, "share": share, **summary}
                )
        else:
            summary = summarize([row.get(metric_key) for row in rows], percentiles)
            if summary:
                records.append({"metric": name, "group": None, **summary})
    return records


def _format_table(headers, rows):
    """Right-align a table, left-aligning only the first (label) column."""
    columns = list(zip(*([headers] + rows))) if rows else [[h] for h in headers]
    widths = [max(len(str(cell)) for cell in col) for col in columns]

    def line(cells):
        return "  ".join(
            str(cell).ljust(widths[i]) if i == 0 else str(cell).rjust(widths[i])
            for i, cell in enumerate(cells)
        )

    return "\n".join(line(row) for row in [headers] + rows)


def report_stats(records, metric_names, group_by, percentiles, out_path):
    """Print the stats table(s) to stderr, and optionally write them as CSV.

    Grouped output carries a `share` column (percent of rows in that group);
    the ungrouped overview does not, since it would always be 100.
    """
    pcols = [f"p{p:g}" for p in percentiles]
    # `share` sits right after `n` when grouping.
    stat_cols = (
        (["n", "share"] if group_by else ["n"]) + ["min", "mean"] + pcols + ["max"]
    )

    def group_label(value):
        return "(none)" if value is None else str(value)

    if group_by:
        for name in metric_names:
            group_rows = [r for r in records if r["metric"] == name]
            if not group_rows:
                continue
            print(f"\nmetric: {name}   group-by: {group_by}", file=sys.stderr)
            headers = [group_by] + stat_cols
            table = [
                [group_label(r["group"])] + [str(r[c]) for c in stat_cols]
                for r in group_rows
            ]
            print(_format_table(headers, table), file=sys.stderr)
    elif records:
        print("\nboot time distribution (seconds):", file=sys.stderr)
        headers = ["metric"] + stat_cols
        table = [[r["metric"]] + [str(r[c]) for c in stat_cols] for r in records]
        print(_format_table(headers, table), file=sys.stderr)

    if out_path:
        with open(out_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["metric", "group"] + stat_cols)
            for r in records:
                group = "" if r["group"] is None else r["group"]
                writer.writerow([r["metric"], group] + [r[c] for c in stat_cols])
        print(f"wrote {out_path}", file=sys.stderr)


def collect_extremes(spawns, metric_names, n, where=()):
    """The n slowest and n fastest rows behind each metric.

    Rows with no value for the metric are dropped, as they are from the summary,
    so the ends of these lists are the `min` and `max` the stats table reports.

    Returns [(metric, grain, slowest, fastest)], slowest worst-first and fastest
    best-first.
    """
    listings = []
    for name in metric_names:
        grain, metric_key = METRICS[name]
        rows = [
            r
            for r in select_rows(spawns, grain, where)
            if r.get(metric_key) is not None
        ]
        if not rows:
            continue
        rows.sort(key=lambda r: r[metric_key])
        listings.append((name, grain, list(reversed(rows[-n:])), rows[:n]))
    return listings


def format_rows(grain, rows):
    """One row per line, with the columns that explain a fast or slow spawn."""
    columns = EXTREME_COLS[grain]
    table = []
    for row in rows:
        cells = []
        for column in columns:
            value = row.get(column)
            if column in ("image", "slowest_image"):
                value = short_image(value)
            cells.append("" if value is None else value)
        table.append(cells)
    return _format_table(columns, table)


def report_extremes(listings):
    """Print the rows at both ends of each metric's distribution."""
    for name, grain, slowest, fastest in listings:
        print(f"\nslowest {len(slowest)} by {name}:", file=sys.stderr)
        print(format_rows(grain, slowest), file=sys.stderr)
        print(f"\nfastest {len(fastest)} by {name}:", file=sys.stderr)
        print(format_rows(grain, fastest), file=sys.stderr)


def resolve_stats_options(metric, group_by, percentiles, where):
    """Turn the raw stats flags into (metric_names, percentiles, where_clauses).

    Fails fast with click.UsageError on a bad value, so a typo is caught before
    we spend time fetching from CloudWatch.
    """
    try:
        percentiles = [float(p) for p in percentiles.split(",") if p.strip()]
    except ValueError:
        raise click.UsageError("--percentiles must be numbers")
    if not percentiles or any(not 0 <= p <= 100 for p in percentiles):
        raise click.UsageError("--percentiles must be between 0 and 100")

    group_grain = GROUP_DIMS[group_by][0] if group_by else None
    if metric:
        metric_names = [m.strip() for m in metric.split(",") if m.strip()]
        unknown = [m for m in metric_names if m not in METRICS]
        if unknown:
            raise click.UsageError(
                f"unknown --metric {','.join(unknown)}; choose from {', '.join(METRICS)}"
            )
    elif group_grain == "pull":
        metric_names = ["pull"]
    elif group_by:
        # One metric keeps a grouped table readable; widen it with --metric.
        metric_names = ["total"]
    else:
        metric_names = ["total", "node_wait", "image_pull", "other"]

    # A group-by dimension has to live on the same grain as the metric ("both"
    # dimensions, including the day/week time buckets, pair with either).
    if group_by and group_grain != "both":
        for name in metric_names:
            metric_grain = METRICS[name][0]
            if metric_grain != group_grain:
                raise click.UsageError(
                    f"--group-by {group_by} is a {group_grain}-level dimension "
                    f"but --metric {name} is {metric_grain}-level; they can't be combined"
                )

    metric_grains = {METRICS[n][0] for n in metric_names}
    where_clauses = []
    for clause in where:
        if "=" not in clause:
            raise click.UsageError(f"--where must be KEY=VALUE, got {clause!r}")
        key, value = clause.split("=", 1)
        key = key.strip()
        if key not in WHERE_DIMS:
            raise click.UsageError(
                f"unknown --where key {key!r}; choose from {', '.join(WHERE_DIMS)}"
            )
        key_grain = WHERE_DIMS[key][0]
        if key_grain != "both" and key_grain not in metric_grains:
            raise click.UsageError(
                f"--where {key} is a {key_grain}-level field but the selected "
                f"metric(s) are {'/'.join(sorted(metric_grains))}-level"
            )
        where_clauses.append((key, value))

    return metric_names, percentiles, where_clauses


@click.command(help=__doc__)
@click.option("--cluster", help="Cluster name, used to derive the log group")
@click.option("--from-file", help="File of events, one JSON object per line")
@click.option("--log-group", help="Override the derived /2i2c/<cluster>/k8s-events")
@click.option("--region", default="us-west-2", show_default=True)
@click.option(
    "--hours", type=int, default=24, show_default=True, help="How far back to look"
)
@click.option(
    "--concurrency",
    type=int,
    default=4,
    show_default=True,
    help="Fetch this many CloudWatch time shards in parallel. Higher is faster "
    "on wide --hours windows, until FilterLogEvents throttles.",
)
@click.option(
    "--namespace", help="Only look at one hub's namespace, e.g. staging or prod"
)
@click.option(
    "--no-server-filter",
    is_flag=True,
    help="Fetch every event and filter locally. Use this if the server-side "
    "filter returns nothing because the stored records aren't shaped as we expect",
)
@click.option("--out", help="Write spawn rows to this CSV instead of stdout")
@click.option("--per-image", help="Also write a row-per-image-pull CSV here")
@click.option(
    "--metric",
    help="Comma-separated metrics to summarise: "
    + ", ".join(METRICS)
    + ". Defaults to all spawn metrics, or 'pull' when grouping by image/cached.",
)
@click.option(
    "--group-by",
    type=click.Choice(sorted(GROUP_DIMS)),
    help="Break the stats down by this dimension, e.g. instance_type, image, or day",
)
@click.option(
    "--where",
    multiple=True,
    metavar="KEY=VALUE",
    help="Keep only rows matching this before summarising, e.g. "
    "instance_type=r5.xlarge. Repeatable (all must match).",
)
@click.option(
    "--percentiles",
    default="50,90,95,99",
    show_default=True,
    help="Comma-separated percentiles to report",
)
@click.option(
    "--extremes",
    type=int,
    default=0,
    metavar="N",
    help="Also list the N slowest and N fastest rows behind each metric, with "
    "the fields that explain them: node type, cold start, where the time went",
)
@click.option(
    "--max-total",
    type=float,
    metavar="SECONDS",
    help="Leave spawns whose total_s is above this out of the stats and the "
    "extremes, and print what was left out. A backstop for implausible rows; "
    "the CSVs still hold every spawn.",
)
@click.option("--stats-out", help="Also write the stats table as CSV here")
@click.option(
    "--inspect",
    is_flag=True,
    help="Print the keys of the first event and exit, to check the shape of what we're storing",
)
def main(
    cluster,
    from_file,
    log_group,
    region,
    hours,
    concurrency,
    namespace,
    no_server_filter,
    out,
    per_image,
    metric,
    group_by,
    where,
    percentiles,
    extremes,
    max_total,
    stats_out,
    inspect,
):
    if bool(cluster) == bool(from_file):
        raise click.UsageError("provide exactly one of --cluster or --from-file")

    metric_names, percentiles, where_clauses = resolve_stats_options(
        metric, group_by, percentiles, where
    )

    if from_file:
        events = load_events_from_file(from_file)
    else:
        log_group = log_group or f"/2i2c/{cluster}/k8s-events"
        # --inspect exists to show us how the records are actually shaped, so it
        # must not depend on a pattern that assumes that shape already.
        pattern = (
            None
            if no_server_filter or inspect
            else cloudwatch_filter_pattern(namespace)
        )
        if pattern:
            print(f"cloudwatch filter: {pattern}", file=sys.stderr)
        events = load_events_from_cloudwatch(
            log_group, region, hours, pattern, concurrency
        )

    if inspect:
        for event in events:
            print(json.dumps(event, indent=2, sort_keys=True))
            return
        print("No events found", file=sys.stderr)
        return

    grouped = defaultdict(list)
    total_seen = 0
    seen_events = set()
    duplicates = 0
    for event in events:
        total_seen += 1
        involved = event.get("involvedObject", {})
        name = involved.get("name") or ""
        if not USER_POD_RE.match(name):
            continue
        if namespace and involved.get("namespace") != namespace:
            continue
        key = dedup_key(event)
        if key in seen_events:
            duplicates += 1
            continue
        seen_events.add(key)
        ts = event_time(event)
        if ts is None:
            continue
        event["_ts"] = ts
        grouped[spawn_key(event)].append(event)

    spawns = [summarise_spawn(evts) for evts in grouped.values()]
    # Drop spawns we only caught the tail of - without a Scheduled event we
    # can't say anything useful about where the time went.
    spawns = [s for s in spawns if s["total_s"] is not None]
    spawns.sort(key=lambda s: s["started_at"] or "")

    print(
        f"{total_seen} events -> {len(grouped)} user pods -> {len(spawns)} complete spawns",
        file=sys.stderr,
    )
    if duplicates:
        print(
            f"dropped {duplicates} duplicate events "
            f"({duplicates / total_seen:.0%} of what we fetched). Around half "
            f"means the collector is re-shipping: check that fluent-bit's "
            f"kubernetes_events input has DB set",
            file=sys.stderr,
        )
    if total_seen == 0 and not from_file and not no_server_filter:
        # A pattern that doesn't match the stored shape looks exactly like an
        # idle cluster, so say which one we can't tell apart.
        print(
            "No events matched. Either nothing spawned in this window, or the "
            "records aren't shaped as the filter assumes - re-run with "
            "--no-server-filter, or with --inspect to see one raw record.",
            file=sys.stderr,
        )
    if not spawns:
        return

    columns = [c for c in spawns[0] if not c.startswith("_")]
    if out:
        with open(out, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for spawn in spawns:
                writer.writerow({c: spawn[c] for c in columns})
        print(f"wrote {out}", file=sys.stderr)
    else:
        writer = csv.DictWriter(sys.stdout, fieldnames=columns)
        writer.writeheader()
        for spawn in spawns:
            writer.writerow({c: spawn[c] for c in columns})

    if per_image:
        with open(per_image, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "pod",
                    "started_at",
                    "instance_type",
                    "image",
                    "duration_s",
                    "size_bytes",
                    "cached",
                ]
            )
            for spawn in spawns:
                for pull in spawn["_pulls"]:
                    writer.writerow(
                        [
                            spawn["pod"],
                            spawn["started_at"],
                            spawn["instance_type"],
                            pull["image"],
                            (
                                round(pull["duration_s"], 3)
                                if pull["duration_s"] is not None
                                else None
                            ),
                            pull["size_bytes"],
                            pull["cached"],
                        ]
                    )
        print(f"wrote {per_image}", file=sys.stderr)

    # Everything above wrote out every spawn we reconstructed. What we
    # summarise below can be narrower, so an implausible row doesn't decide what
    # the mean looks like - but say which rows those were.
    summarised = spawns
    if max_total is not None:
        summarised = [s for s in spawns if s["total_s"] <= max_total]
        excluded = [s for s in spawns if s["total_s"] > max_total]
        if excluded:
            excluded.sort(key=lambda s: s["total_s"], reverse=True)
            print(
                f"\nleft {len(excluded)} spawn(s) out of the stats, total_s "
                f"above {max_total:g}s:",
                file=sys.stderr,
            )
            print(format_rows("spawn", excluded), file=sys.stderr)

    # A quick read on where time goes, so the common case needs no extra tooling.
    records = compute_stats(
        summarised, metric_names, group_by, percentiles, where_clauses
    )
    report_stats(records, metric_names, group_by, percentiles, stats_out)

    if extremes:
        report_extremes(
            collect_extremes(summarised, metric_names, extremes, where_clauses)
        )


if __name__ == "__main__":
    main()
