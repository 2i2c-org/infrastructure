# Create a new GCP project

1. [Create new project under the 2i2c GCP org](https://console.cloud.google.com/projectcreate?previousPage=%2Fhome%2Fdashboard%3Fproject%3Dtwo-eye-two-see%26organizationId%3D0&organizationId=184174754493).
   This lets us do access control more easily, and makes sure 2i2c engineers always
   have appropriate access to the created project.
2. Name the project, giving it a unique id. We try to keep the word '2i2c' out
   of the project name, in case the user decide to exercise their [right to
   replicate](https://2i2c.org/right-to-replicate/) at some point.
3. Keep it inside the 2i2c organization, and locate inside the 2i2c folder.
4. Use the two-eye-two-see billing account.
5. Hit the 'Create' button
6. You should see a notification as soon as the project is created. Switch to the freshly
   created project
7. GCP requires you to explicitly [enable APIs](https://cloud.google.com/apis/docs/getting-started#enabling_apis)
   before they can be used. Enable the following APIs:
   1. [GKE](https://console.cloud.google.com/apis/library/container.googleapis.com)
   2. [Compute Engine](https://console.cloud.google.com/apis/api/compute.googleapis.com/overview)
   3. [Artifact Registry](https://console.cloud.google.com/apis/library/artifactregistry.googleapis.com)
   4. [Filestore](https://console.cloud.google.com/apis/api/file.googleapis.com/overview)

   ```{note}
   Make sure the correct project is selected while enabling these!
   ```

8. [Setup a new cluster](new-cluster:new-cluster) inside it via Terraform
