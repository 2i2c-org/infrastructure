# Update environment

The user environments is specified via a `Dockerfile`, under `images/user` in
the git repository. Currently there is no automated image building - so you will
have to manually build & push it after making a change.

1. Install pre-requisites:
   * Docker
   * A Python virtual environment. Install `requirements.txt` into it.
   * The `gcloud` tool, authenticated to the `two-eye-two-see` project.
      You need to run `gcloud auth configure-docker us-central1-docker.pkg.dev`
      once as well.

2. Make the changes you need to make to the environment, and git commit it.

3. Run `python3 deployer build <cluster-name>`, once for each `<cluster>` under `config/hubs`.
   This will build the image and push it to registry. It will tell you what the generated image tag is.

4. Update `jupyterhub.singleuser.image.tag` in `hub-templates/base-hub/values.yaml` with this tag.

5. Make a commit, make a PR and merge to master! This will deploy all the hubs
   with the new image
