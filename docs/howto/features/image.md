# Enable user image features

This document points to various other bits of documentation on how
to enable various features that involve modifying the user image. We should
keep the documentation here fairly minimal, as it should all be upstream
wherever possible.

## Mount object storage as files with FUSE

```{warning}

Consider [if you actually will benefit from it](https://github.com/yuvipanda/jupyterhub-roothooks/#should-you-do-it)
before you do it
```

[jupyterhub-roothooks](https://github.com/yuvipanda/jupyterhub-roothooks/)
can be used to setup object storage (S3, GCS, etc) as paths on the filesystem
via FUSE.

This is mounted from inside the user pod, so will use whatever
cloud permissions the user has. So to provide write access or access
to private object storage buckets, we will need to configure
[appropriate cloud permissions](
howto:features:cloud-access:access-perms). However, for just
public object storage buckets, no extra permissions are needed.