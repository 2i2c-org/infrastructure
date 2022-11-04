# Build a Docker Image remotely

Docker images with datascience related packages can be *huge*, and very
difficult to build locally! We run a remote [docker-in-docker hack](https://gist.github.com/yuvipanda/48100eb9e15dae808052c7dc9fb22edb)
on our 2i2c cluster to make this a lot more painless. This document describes
*how* you can use this to build docker images from your laptop much faster.
This frees up your laptop's resources, as well as provides you with a datacenter
scale upload / download speeds.

## Building images remotely

1. From a clone of the `infrastructure` repository, get yourself appropriate credentials
   for the `2i2c` cluster.

   ```bash
   deployer use-cluster-credentials 2i2c
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

## Testing images remotely

Now that the image has been built remotely, how do you *test* it? Ideally, we would be
able to run a container with the built image, run `jupyterlab` inside it, and test some
stuff up. Can we still do it even with the docker daemon running remotely?

Yes, we can!

1. Open a new terminal, and make sure you are authenticated to the 2i2c cluster.

   ```bash
   deployer use-cluster-credentials 2i2c
   ```

2. Now, let's assume the image you built and want to test is called `test-image:v1`. This
   can be any image name, including something that is being pulled from a remote repository.
   Execute the following code on your terminal

   ```bash
   # The name of the image we wanna test
   IMAGE_NAME=test-image:v1
   # The DIND pod running in the default namespace
   DIND_POD_NAME=$(kubectl get pod -l app=dind -o name)
   # Now, we execute a docker commandline command from inside this dind pod!
   # We start jupyter lab, and forward the port 9999 from inside that container inside
   # the docker daemon running inside the kubernetes pod to just inside the kubernetes pod.
   # We've essentially peeled behind one layer of our container onion.
   # if you get a port conflict, try a different port!
   PORT=9999
   kubectl exec -it \
        ${DIND_POD_NAME} \
        -- \
        /bin/sh -c \
        "DOCKER_HOST=tcp://127.0.0.1:2376 docker run -it -p ${PORT}:${PORT} ${IMAGE_NAME} jupyter lab --ip=127.0.0.1 --port=${PORT}"
    ```

    This should produce output that looks like:

    ```
        To access the notebook, open this file in a browser:
        file:///home/jovyan/.local/share/jupyter/runtime/nbserver-1-open.html
    Or copy and paste one of these URLs:
        http://127.0.0.1:9999/?token=9a078a60238ac7454107c55a369829f7c1f228b9b2803193
     or http://127.0.0.1:9999/?token=9a078a60238ac7454107c55a369829f7c1f228b9b2803193
    ```

    The first line won't be useful, but the second two (which should be the same!) are what we need.
    However, one more step is needed before we can access these!

3. Open yet another terminal, and make sure you are authenticated to the 2i2c cluster (follow step 1).

4. Now in *this* terminal, run:

   ```bash
   # Should match PORT set in step 2
   PORT=9999
   kubectl port-forward deployment/dind ${PORT}:${PORT}
   ```

   This establishes a port-forward from your local machine at port 9999 (or whatever `PORT` is) to the
   jupyter lab running inside the container inside the kubernetes pod on the remote cluster!

5. *Now* Go to the URL you found in step (2), and it should give you a jupyter lab instance in the
   browser! RStudio, Linux Desktop, etc should also work if they are in the image.


## Limitations

This *does* come with some limitations.

1. When the server is started on JupyterHub, `$HOME` inside the container is overwritten by
   the user's home directory and that persists. When testing using the method listed here,
   the `$HOME` in the container image is shown as is. This might lead (in some very limited circumstances)
   to things that work while we test here but not in the hub. If `$HOME` is not empty when
   you open it this way, you should find and fix it such that it is!
2. https://xkcd.com/1172/