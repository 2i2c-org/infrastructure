# Build a Docker Image remotely

Docker images with datascience related packages can be *huge*, and very
difficult to build locally! We run a remote [docker-in-docker hack](https://gist.github.com/yuvipanda/48100eb9e15dae808052c7dc9fb22edb)
on our 2i2c cluster to make this a lot more painless. This document describes
*how* you can use this to build docker images from your laptop much faster.
This frees up your laptop's resources, as well as provides you with a datacenter
scale upload / download speeds.

1. From a clone of the `infrastructure` repository, get yourself appropriate credentials
   for the `2i2c` cluster.

   ```bash
   python3 deployer use-cluster-credentials 2i2c
   ```

   This should set your current context to be that of the 2i2c cluster.

2. Port-forward to the docker daemon running in the `default` namespace. This is a
   `kubectl apply` of the contents of [this gist](https://gist.github.com/yuvipanda/48100eb9e15dae808052c7dc9fb22edb).

   ```bash
   kubectl port-forward deployment/dind 23760:2376
   ```

   This will forward your *local* computer's port `23760` to the port `2376` running
   inside the `dind` deployment on the default namespace. There is a docker daemon
   running on that port, so essentially this looks like you have a docker daemon
   running locally on your system at port `23760` but it's actually running in our
   kubernetes cluster!

   This command will block, and you will have to start it again if you have a network
   interruption.

3. In another terminal, you need to tell tools to use this new port-forwarded port
   as the docker daemon. You can do this by setting the `DOCKER_HOST` environment variable.

   ```bash
   export DOCKER_HOST=tcp://localhost:23760
   ```

4. Verify that the remote docker daemon is what is used by running `docker
   info`. You should see something like `Name: dind-<random-chars>` - this verifies
   it's running on the remote cluster!

5. Now you can run any tool (like `repo2docker`, `chartpress` or just `docker build`) as you
   wish, and they will all automatically talk to this remote docker instance! Hurrah!

## Limitations

This *does* come with some limitations.

1. No volume mounting is available, as the docker daemon is running remotely
2. Port forwards within this port-forward are totally possible, thus allowing the ability
   to actually *test* the built images without having to push them to dockerhub. However,
   this hasn't been tried or documented yet.
3. https://xkcd.com/1172/