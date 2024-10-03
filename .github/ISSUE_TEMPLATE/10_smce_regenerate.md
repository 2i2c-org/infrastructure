---
name: "🔐 Regenerate NASA SMCE credentials"
about: Recurring task that must be done every ~55 days
title: "[ {{Deadline}} ] Regenerate NASA SMCE credentials"
labels: ["recurrent"]
---

The credentials of the deployer on SMCE clusters must be renewed every ~55 days. 

_Once all the info has been filled in, this issue is considered to be fully refined and can be added to the `Refined` column of the Project Board._

### Context

AWS credentials for our hub deployer must be renewed for the following clusters:

- [ ] nasa-veda
- [ ] nasa-ghg
- [ ] nasa-esdis

### Resources
Follow [the instructions](https://infrastructure.2i2c.org/howto/regenerate-smce-creds/#regenerate-credentials-for-the-deployer) on how to do this.

https://github.com/2i2c-org/infrastructure/issues/4577 was the previous time this was done.

### Definition of Done
```[tasklist]
- [ ] There is a deadline for this task -> yes, Oct 3
- [ ] The credentials of the deployer on all 3 clusters have been renewed
```