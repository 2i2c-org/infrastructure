# Set up a hub for an exam

We provide support for using a JupyterHub in a *controlled* physical
space for exams. This is an extra paid feature where we charge hourly
for responsiveness.

This page documents what we do to prep, based on our prior experiences.

1. **Exact dates and times are known and at least two engineers available**

   Make sure the exact dates and times of the exam are checked well in
   advance, and we have at least two engineers available during this time period.

2. **Check engineer access**

   Engineers should *test* their access to the infrastructure and the
   hub beforehand, to make sure they can fix issues if needed.

   Simple checklist:
      - 🔲 Access and login to the hub admin page
      - 🔲 Access and login to the cluster grafana
      - 🔲 Access and login to the cloud console
      - 🔲 Test access to Logs Explorer for container logs if on GCP
      - 🔲 Test that running `deployer use-cluster-credentials $CLUSTER_NAME` and then `kubectl get pods -A` work

3. **Ensure user pods have a guaranteed quality of service class**

   For the duration of the exam, all user pods must have a
   [guaranteed quality of service class](https://kubernetes.io/docs/tasks/configure-pod-container/quality-service-pod/).

   In practice, this means we have memory & cpu requests set to be the same
   as guarantees. This is to ensure equity - no user should get more or less
   resources than any other. It also improves reliability.

   This usually increases cost too, so should be done **no more than 12h before**
   the start of the exam. It should be reverted back soon after the exam
   is done.

   If the hub has a profile list enabled, based on the instance types setup for
   the hub, you can find the new allocation options by running:

   ```bash
   deployer generate resource-allocation choices <instance-type>
   ```

   Running this command will output options where memory requests equal limits.

4. **Ensure instructor tests the hub before the exam**

   The instructor running the exam should test out their exam on the hub,
   and make sure that it will complete within the amount of resources assigned
   to it. They should also make sure that the environment (packages, python
   versions, etc) are set up appropriately. From the time they test this until
   the exam is over, new environment changes are put on hold.

   Responsibilities:
      - the **community and partnerships** team makes sure that the community's
      **expectations** around exams are correctly set
      - the **engineer(s)** leading the exam, should make sure **they are respected**

5. **Pre-warm the cluster**

   We should pre-warm the cluster the hub is on before the start of the exam,
   to make sure that all users can start a notebook without having to wait. This
   is also for equity reasons, to make sure we don't disadvantage one user from
   another.

6. **Follow freshdesk for any questions/issues**

   Issues during the exam are communicated via freshdesk, and what we are paid
   for is to make sure we respond immediately - there is no guarantee of fixes,
   although we try very hard to make sure the infrastructure is stable during this
   period.
