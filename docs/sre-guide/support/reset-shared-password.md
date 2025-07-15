# Reset password for shared password hubs

Some hubs have [shared password authentication](../../hub-deployment-guide/configure-auth/shared-password.md) enabled. This allows users to log in with a shared password, which is useful for workshops and other events. If you need to reset the shared password, follow these steps.

## Process

1. A community will usually indicate that they require a shared password reset for an event through FreshDesk support.
1. Acknowledge receipt of the request and confirm the password to be used and the implementation date, as well as event details.
1. Open an [Event for a community](https://github.com/2i2c-org/infrastructure/issues/new?template=07_event-hub.yaml) issue in the infrastructure repository and follow the instructions. Remember to add the event to the [Hub Events calendar](https://calendar.google.com/calendar/u/2?cid=Y19rdDg0c2g3YW5tMHNsb2NqczJzdTNqdnNvY0Bncm91cC5jYWxlbmRhci5nb29nbGUuY29t).
1. Add a sub-issue of the event issue to reset the shared password. This sub-issue should be titled "[`$CLUSTER_NAME`, `$HUB_NAME`] Reset shared password".
1. Add the sub-issue to the GH project board with the "End date" set to the date.
1. Before the "End date", reset the shared password and update the issue with the new password by using the `sops` command to edit the password key of the `config/clusters/$CLUSTER_NAME/${HUB_NAME}.secret.values.yaml` file

   ```bash
    sops edit enc-${HUB_NAME}.secret.values.yaml
   ```

   :::{note}
    You will need to authenticate with `gcloud auth login` and `gcloud auth application-default login` before running the `sops` command.
   :::

1. Once the change has been implemented, notify the hub administrators to confirm the password has been reset and that they should test it.
1. Close the sub-issue once the password has been confirmed to be working.
1. Close the event issue once the event has concluded.
