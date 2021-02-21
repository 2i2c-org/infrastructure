---
name: "\U0001F4DD Debrief / post-mortem"
about: Discuss what happened + next steps after an event.
title: Debrief - {{ TITLE }}
labels: post-mortem
assignees: ''

---

# Summary

Quick summary of what user impact was, how long it was, and how we fixed it.

## Timeline (if relevant)

If it makes sense to include a timeline for this debrief, then do so below. This is usually most-useful for post-mortems.

All times in {{ most convenient timezone}}.

### {{ yyyy-mm-dd hh:mm }}

Start of incident. First symptoms, possibly how they were identified.

### {{ hh:mm }}

Investigation starts.

### {{ hh:mm }}

More details.

## What went wrong

Things that could have gone better. Ideally these should result in concrete
action items that have GitHub issues created for them and linked to under
Action items. For example,

1. We do not record the number of hub spawn errors in a clear and useful way,
   and hence took a long time to find out that was happening.
2. Our culler process needs better logging, since it is somewhat opaque now
   and we do not know why restarting it fixed it.
3. Our documentation was misleading or unclear, and so user expectations weren't correct.

## Where we got lucky

These are good things that happened to us but not because we had planned for them.
For example,

1. We noticed the outage was going to happen a few minutes before it did because
   we were watching logs for something unrelated.
2. The one person that knew how to fix this happened to be the one paying attention at that moment.

## Action items

These are only sample subheadings. Every action item should have a GitHub issue
(even a small skeleton of one) attached to it, so these do not get forgotten. These issues don't have to be in `pilot-hubs/`, they can be in other repositories.

### Process improvements

1. {{ summary }} [link to github issue]
2. {{ summary }} [link to github issue]

### Documentation improvements

1. {{ summary }} [link to github issue]
2. {{ summary }} [link to github issue]

### Technical improvements

1. {{ summary }} [link to github issue]
2. {{ summary }} [link to github issue]
