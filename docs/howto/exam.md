# Set up a hub for an exam

We provide support for using a JupyterHub in a *controlled* physical
space for exams. This is an extra paid feature where we charge hourly
for responsiveness.

This page documents what we do to prep, based on our prior experiences.

1. Make sure the exact dates and times of the exam are checked well in
   advance, and we have enough engineering coverage during this time period.
   Engineers should also *test* their access to the infrastructure and the
   hub beforehand, to make sure they can fix issues if needed.

2. For the duration of the exam, all user pods must have a
   [guaranteed quality of service class](https://kubernetes.io/docs/tasks/configure-pod-container/quality-service-pod/).
   In practice, this means we have memory & cpu requests set to be the same
   as guarantees. This is to ensure equity - no user should get more or less
   resources than any other. It also improves reliability.

   This usually increases cost too, so should be done no more than 12h before
   the start of the exam. It should be reverted back soon after the exam
   is done.

3. The instructor running the exam should test out their exam on the hub,
   and make sure that it will complete within the amount of resources assigned
   to it. They should also make sure that the environment (packages, python
   versions, etc) are set up appropriately. From the time they test this until
   the exam is over, new environment changes are put on hold.

4. We should pre-warm the cluster the hub is on before the start of the exam,
   to make sure that all users can start a notebook without having to wait. This
   is also for equity reasons, to make sure we don't disadvantage one user from
   another.

5. Issues during the exam are communicated via freshdesk, and what we are paid
   for is to make sure we respond immediately - there is no guarantee of fixes,
   although we try very hard to make sure the infrastructure is stable during this
   period.
