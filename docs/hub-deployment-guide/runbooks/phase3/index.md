(hub-deployment-guide:runbooks:phase3)=
# Phase 3: Hub setup

This assumes a cluster where the hub will be deployed to already exists

## Phase 3.1: Initial setup

### Definition of ready

The following lists the information that needs to be available to the engineer before this phase can start.

- Name of the hub
- Dask gateway?
- Splash image
- URL: That will be used for both URL and funded_by
- Authentication Mechanism
- Admin Users

### Outputs

At the end of Phase 3.1 both 2i2c engineers and the admin users mentioned can login to the hub.

The file assets that should have been generated and included in the PR should be:

```bash
```

```{tip}
When reviewing cluster setup PRs, make sure the files above are all present.
```

### Hub setup runbook

All of the following steps must be followed in order to consider phase 3.1 complete. Steps might contain references to other smaller, topic-specifc runbooks that are gathered together and listed in the order they should be carried on by an engineer.

