# 2i2c Pilot Hubs Infrastructure

This is documentation for the 2i2c Pilot Hubs deployment infrastructure. The goal of this stack is to automatically deploy JupyterHubs in the cloud from a single `hubs.yaml` configuration file.

All hub configuration is in `hubs.yaml`. You can add a new hub by adding
an entry there, and pushing that to github.

```{toctree}
configure
operate
custom-image
incidents/index
```

## How we plan to use this repository

Currently, most user-facing documentation for the Hubs Pilot is at [2i2c.org/pilot](https://2i2c.org/pilot/). We'll use the following repositories for managing users and maintenance of these hubs:

- [github.com/2i2c-org/pilot](https://github.com/2i2c-org/pilot) - point-of-contact with users. User documentation. Questions, requests, problems, etc.
- [github.com/2i2c-org/pilot-hubs](https://github.com/2i2c-org/pilot-hubs) - Hub deployment information, issues for maintenance and technical enhancements on the hubs.

We've asked users to submit any questions, problems, requests, etc as issues via [github.com/2i2c-org/pilot](https://github.com/2i2c-org/pilot) using issue templates. **Hub operators** should triage these issues, and surface any that require ongoing attention as issues in the [github.com/2i2c-org/pilot-hubs](https://github.com/2i2c-org/pilot-hubs) repository. This includes technical problems that need fixes, as well as requests such as environment updates.

2i2c Hub Operators as well as Hub Architects shall use this repository to perform hub updates and maintenance in order to resolve these issues. They'll also use this repository to create new hubs for communities that have reached out via [https://2i2c.org/pilot](https://2i2c.org/pilot).
