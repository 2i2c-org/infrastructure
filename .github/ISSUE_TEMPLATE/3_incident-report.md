---
name: "🚨 Hub Incident"
about: "Report an incident on our running hub infrastructure."
title: "[Incident] {{ TITLE }}"
labels: ["type: Hub Incident", "support"]
assignees: ""
---

### Summary

<!-- Quick summary of the problem and resolution. Update as we learn more -->

### Impact on users

<!-- How this impacts users on the hub. Help us understand how urgent this is. -->

### Important information

<!-- Any links that could help people debug or learn more.  -->

- Hub URL: {{ INSERT HUB URL HERE }}
- Support ticket ref: {{ INSERT SUPPORT REF HERE }}

### Tasks and updates

- [ ] Discuss and address incident, leaving comments below with updates
- [ ] Incident has been dealt with or is over
- [ ] Copy/paste the after-action report below and fill in relevant sections
- [ ] Incident title is discoverable and accurate
- [ ] All actionable items in report have linked GitHub Issues

<!-- A copy/paste-able after-action report to help with follow-up -->
<details>
<summary>After-action report template</summary>

```
# After-action report

These sections should be filled out once we've resolved the incident and know what happened.
They should focus on the knowledge we've gained and any improvements we should take.

## Timeline

_A short list of dates / times and major updates, with links to relevant comments in the issue for more context._

All times in {{ most convenient timezone}}.

- {{ yyyy-mm-dd }} - [Summary of first update](link to comment)
- {{ yyyy-mm-dd }} - [Summary of another update](link to comment)
- {{ yyyy-mm-dd }} - [Summary of final update](link to comment)


## What went wrong

_Things that could have gone better. Ideally these should result in concrete
action items that have GitHub issues created for them and linked to under
Action items._

- Thing one
- Thing two

## Where we got lucky

_These are good things that happened to us but not because we had planned for them._

- Thing one
- Thing two

## Follow-up actions

_Every action item should have a GitHub issue (even a small skeleton of one) attached to it, so these do not get forgotten. These issues don't have to be in `infrastructure/`, they can be in other repositories._

### Process improvements

1. {{ summary }} [link to github issue]
2. {{ summary }} [link to github issue]

### Documentation improvements

1. {{ summary }} [link to github issue]
2. {{ summary }} [link to github issue]

### Technical improvements

1. {{ summary }} [link to github issue]
2. {{ summary }} [link to github issue]
```

</details>
