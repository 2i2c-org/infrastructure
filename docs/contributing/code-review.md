(infrastructure:review)=
# Review and merge guidelines for 2i2c Engineers

## Mindset

This repository is *not* an open source *project* (unlike, for example,
[jupyterhub/jupyterhub](https://github.com/jupyterhub/jupyterhub)). It
is instead the *source of truth* for the infrastructure that 2i2c runs.
As such, it needs a different mindset on what review is **useful**.

When you merge a PR in an open source *project*, usually you have to keep
in mind a lot of factors:

1. How will this affect downstream users?
2. How will this affect me (and other maintainers) in the future as we
   try to change this?
3. How will this affect the direction of the project?

However, when we merge a PR in this *infrastructure repository*, the
factors are quite different:

1. What change will this actually make to our running infrastructure?
2. How do I know it has done the thing I intended it to do?
3. How do we mitigate the chance that we break something unintentionally?

This repository has **no downstream users**, which gives us a fair bit
of flexibility in how we go about it (subject only to restrictions based
on [Right to Replicate](https://2i2c.org/right-to-replicate/)).

## Prime directive

The following should be the prime directive under which we approach
making changes to this repository:

> Better to always move forward in the direction of the iteration / team
> goal, than to not.

(Inspired by [this document in our team compass](https://compass.2i2c.org/engineering/workflow/1-week-iteration-workflow/)).

It's a bias towards action, with the goal of empowering team members
to make progress, learn, break things (safely) and iterate as needed.

As a corollary, the primary role of **code review** is to **help
engineers grow** and build a coherent, high performance team that we can
all trust in, rather than a specific focus on 'the right thing'.

## Before making a PR

Before you make a PR, ask yourself the following questions:

1. Is this PR in service of moving forward on a issue that you picked up
   from the Engineering Board?

If the answer to this is "No", consider if you really *must* do this. The
engineering board is a representation of the work the *team* has committed to
doing. Ask yourself if you can instead be doing something else that can move
this forward. Can this wait, and go through the refinement / sprint planning
process?

See [the guiding principles](https://compass.2i2c.org/engineering/workflow/1-week-iteration-workflow/#guiding-principle-move-the-team-forward)
document for more guidance on what else you can do.

You should break this rule when it makes sense, but do not do so
**casually**. This is an important mechanism by which we can build a
team we can all trust in over

This may make you uncomfortable, and that is ok. Ultimately our goal is to
build a **team we can all trust in**, and this is a very important part
of getting there.

## After making the PR

After you make your PR, ask yourself these three questions:

1. *If* this PR breaks something, do you feel comfortable debugging it **or**
   reverting it to undo the change?
2. Do you know how to *verify* the effects of merging this PR?

If the answer to all these 2 questions are 'yes', you should go ahead
and self merge.

If it breaks, you can revert your PR, make changes, and try again.

Let's now explore the cases when answers to any of these questions are "no".

### I don't feel comfortable debugging this if it breaks

Congratulations, you have unearthed a (possibly scary) opportunity for growing
as an engineer!

A very important component of improving as an engineer is to be in the
following loop:

1. Make a change that breaks
2. Feel uncomfortable (required), and question your life choices that have led
   you to this moment (optional)
3. Remember that you are not an imposter, and while you may not have the
   specific **knowledge** about the issue, you have the **skills** to
   acquire this knowledge and fix the issue.
4. Boldly proceed into this uncertainty, and fix the issue, asking for
   and receiving help from the team as needed.

Note: You can also ask for help *before*.

As a **team**, our goal is to find ways to empower you to feel more
comfortable with things breaking, because you believe you can fix them
when they *do* break.
<a title="Reedy, CC BY-SA 4.0 &lt;https://creativecommons.org/licenses/by-sa/4.0&gt;, via Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Framed_%22I_BROKE_WIKIPEDIA..._THEN_I_FIXED_IT!%22_T-shirt.jpg"><img width="512" alt="Framed &quot;I BROKE WIKIPEDIA... THEN I FIXED IT!&quot; T-shirt" src="https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Framed_%22I_BROKE_WIKIPEDIA..._THEN_I_FIXED_IT%21%22_T-shirt.jpg/512px-Framed_%22I_BROKE_WIKIPEDIA..._THEN_I_FIXED_IT%21%22_T-shirt.jpg?20190318200628"></a>

We don't have a shirt like this, but maybe someday we could :)

### I don't know how to verify if what I did worked

This likely means the issue was not refined enough. You can escalate this by
either:

1. Asking for more specific information in the GitHub issue.
2. Ask in the `#engineering` slack channel for more information.