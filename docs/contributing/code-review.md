# Code review guidelines

This document codifies our guidelines for doing code review
and merging pull requests.

> A Foolish Consistency is the Hobgoblin of Little Minds
> - PEP 8

## Terraform Changes

[Terraform](https://www.terraform.io/) lets us treat our infrastructure
as code, so we can use regular code quality practices (code review,
linters, extensive documentation, etc) to keep the quality of our
infrastructure high. However, it comes with a few caveats:

1. Locally and iteratively testing terraform is impossible - as we
   develop it, the infrastructure is deployed / modified / destroyed
   as we go.
2. Behavior of a bit of terraform code differs based on the current
   state of the infrastructure (as represented in the
   [state file](https://www.terraform.io/docs/language/state/index.html)).
3. While `terraform plan` can tell us what terraform *thinks* it is
   going to do, it might not always succeed. Permission errors or
   organizational restrictions can cause it to fail. Timeouts can happen.
   Runtime errors pop up.

Thanks to all these, it is impossible to accurately gauge the impact of
a terraform code change just from looking at the text nor automatically
deploy it via continuous deployment.

The guiding principles for terraform code review are:

1. Person who writes the code also does the `terraform apply`.
2. Terraform code merged into the repo must already be successfully applied.
3. For new infrastructure, focus of code review is just on infrastructure design review.
4. For existing infrastructure, focus is on both making sure the change
   is minimally disruptive, and on infrastructure design.

### When setting up new infrastructure

For creating *new* infrastructure, the suggested workflow is:

1. Iteratively develop the code locally, testing it with `terraform apply`
   as you go.
2. Start a PR early, and solicit feedback. The primary goal here is to
   do a review of the *infrastructure design*, rather than of any particular
   `terraform plan` output.
3. Once someone else approves your PR, you must:

   1. Destroy the current infra you have setup with `terraform destroy`
   2. `terraform apply` from scratch, so new infra is setup from scratch
      based on the reviewed state of the PR. If things break, amend your
	  PR until it unbreaks. This might solicit adding another cycle of
	  code review.
   3. Self-merge the PR once the infra works as you would like.

   This way, terraform code will have been 'realized' by the time it is
   merged.

## When modifying existing infrastructure

For modifications to *existing infrastructure*, the suggested workflow is:

1. Make a PR with the suggested change, and iterate on it. Try to use just
   `terraform plan` while iterating as much as possible.
2. Post the output of `terraform plan` in your PR for reviewers. We want
   to review the changes to the infrastructure design, but *also* to any
   currently existing resources and how it might impact users.
3. Once approved, `terraform apply` your change, and make sure it works ok.
   If things break, amend your PR (and `terraform apply`) until it unbreaks.
   You might need another cycle of code review.
4. After the change has been successfully performed with `terraform apply`,
   self-merge your PR.
