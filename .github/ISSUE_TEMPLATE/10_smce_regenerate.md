---
name: "🔐 Regenerate NASA SMCE credentials"
about: Recurring task that must be done every ~55 days
title: "[ {{Deadline}} ] Regenerate NASA SMCE credentials"
labels: ["recurrent"]
---

_Once the deadline has been filled in, this issue is considered to be fully refined and can be added to the `Refined` column of the Project Board._

The credentials of the deployer on SMCE clusters must be renewed every ~55 days.

### Context
AWS credentials for our hub deployer must be renewed for the following clusters:
- [ ] nasa-veda
- [ ] nasa-ghg
- [ ] nasa-esdis

### Resources
Follow [the instructions](https://infrastructure.2i2c.org/howto/regenerate-smce-creds/#regenerate-credentials-for-the-deployer) on how to do this.

### Definition of Done
```[tasklist]
- [ ] There is a deadline for this task
- [ ] The credentials of the deployer on all 3 clusters have been renewed
```