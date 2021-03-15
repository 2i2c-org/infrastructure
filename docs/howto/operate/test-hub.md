# Test the hub
You can deploy a new hub, or an existing one using the `deploy.py` script:

* to deploy a specific hub
    ``` bash
    python3 deploy.py deploy <cluster-name> <hub-name>
    ```

* to deploy all pilot hubs:
    ```bash
    python3 deploy.py deploy
    ```

When using the `deploy.py` script, the hub's heath being deployed is checked by default.

```{note}
You can skip the health check by passing the `--skip-hub-health-test` flag to the `deploy.py` script.
```
A hub is marked as "healthy" if it passes the custom template and the health `pytest` tests.

## The custom template test

Each pilot-hub has their own personalized JupyterHub login page. This test makes sure that the hub has loaded its custom login template by checking the presence of the instutional logo in the login page.

```{figure} ../../images/staging-hub-login-page.png
```

## The Hub health test

There are two types of test notebooks are ran on the hub, based on it's type:
* dask specific notebooks - *are ran on the the daskhub hubs*
* simple notebooks - *are ran on all the other types of hubs*

This test, creates a new hub user called `deployment-service-check`, starts a server for them, and runs the test notebooks. It checks that the notebook runs to completion and the output cells have the expected value.
* If the health check passes, then the user's server is stopped and deleted.
* If the health check fails, then their user server will be left running, but it will get deleted together with the user in the next iteration.

```{note}
If the `deploy.py` script is used to deploy all pilot hubs at once, then a failed hub health check will halt all further deployments!
```
