# Build Tools

Environment definition for local development and CI deployment of 2i2c infra.
Dependency ranges are chosen to avoid drift of key dependencies, and a lockfile used
to secure and speed up deployments.

```bash
conda-lock --kind lock -f environment.yaml -p linux-64
```
