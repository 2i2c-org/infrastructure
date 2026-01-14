# CloudBank Hub Setup Workflow Guide

This guide provides step-by-step instructions for setting up a new JupyterHub in the CloudBank cluster.

## Prerequisites

- Clone of the 2i2c infrastructure repository
- Access to encrypted secrets (sops and PGP keys configured)
- Environment setup: `conda activate infrastructure && pip install -e .`

## Hub Setup Steps

### 1. Create Hub Values File

Create a new file: `config/clusters/cloudbank/{hub_name}.values.yaml`

**Template based on institution details:**

```yaml
jupyterhub:
  ingress:
    hosts: [{hub_name}.cloudbank.2i2c.cloud]
    tls:
    - hosts: [{hub_name}.cloudbank.2i2c.cloud]
      secretName: https-auto-tls
  singleuser:
    memory:
      guarantee: 512M
      limit: 1G
  custom:
    2i2c:
      add_staff_user_ids_of_type: google
      add_staff_user_ids_to_admin_users: true
    homepage:
      templateVars:
        designed_by:
          name: 2i2c
          url: https://2i2c.org
        funded_by:
          name: CloudBank
          url: http://cloudbank.org/
        operated_by:
          name: CloudBank
          url: http://cloudbank.org/
        org:
          logo_url: {LOGO_URL}
          name: {INSTITUTION_NAME}
          url: {INSTITUTION_WEBSITE}
  hub:
    config:
      JupyterHub:
        authenticator_class: cilogon
      CILogonOAuthenticator:
        oauth_callback_url: https://{hub_name}.cloudbank.2i2c.cloud/hub/oauth_callback
        allowed_idps:
          {IDP_URN}:
            default: true
            username_derivation:
              username_claim: email
            allow_all: true
          http://google.com/accounts/o8/id:
            username_derivation:
              username_claim: email
      Authenticator:
        admin_users:
        - sean.smorris@berkeley.edu
        - ericvd@berkeley.edu
        - {ADMIN_EMAIL}
jupyterhub-home-nfs:
  gke:
    volumeId: projects/cb-1003-1696/zones/us-central1-b/disks/hub-nfs-homedirs-{hub_name}
nfs:
  pv:
    serverIP: storage-quota-home-nfs.{hub_name}.svc.cluster.local
```

**Parameters to customize:**
- `{hub_name}`: Lowercase institution identifier (e.g., `uchicago`)
- `{INSTITUTION_NAME}`: Full institution name (e.g., `University of Chicago`)
- `{INSTITUTION_WEBSITE}`: Institution home URL
- `{LOGO_URL}`: Direct link to institution logo (typically SVG or WebP)
- `{IDP_URN}`: InCommon federation identity provider URN (e.g., `urn:mace:incommon:uchicago.edu`)
- `{ADMIN_EMAIL}`: Hub administrator email address

---

### 2. Add Hub Entry to cluster.yaml

Edit: `config/clusters/cloudbank/cluster.yaml`

Add entry in **alphabetical order** under the `hubs:` section:

```yaml
- name: {hub_name}
  display_name: {INSTITUTION_NAME}
  domain: {hub_name}.cloudbank.2i2c.cloud
  helm_chart: basehub
  helm_chart_values_files:
  - common.values.yaml
  - {hub_name}.values.yaml
  - enc-{hub_name}.secret.values.yaml
```

**Example** (University of Chicago, placed between `ucsc` and `virginia`):
```yaml
- name: uchicago
  display_name: University of Chicago
  domain: uchicago.cloudbank.2i2c.cloud
  helm_chart: basehub
  helm_chart_values_files:
  - common.values.yaml
  - uchicago.values.yaml
  - enc-uchicago.secret.values.yaml
```

---

### 3. Create CILogon OAuth Client

Run the deployer command to create encrypted CILogon credentials:

```bash
cd /Users/sean/Documents/cloudbank/infrastructure
conda activate infrastructure
deployer cilogon-client create cloudbank {hub_name} {hub_name}.cloudbank.2i2c.cloud
```

**What this does:**
- Authenticates with 2i2c's CILogon admin credentials (from `shared/deployer/enc-auth-providers-credentials.secret.yaml`)
- Registers a new OAuth client application with CILogon
- Creates and encrypts `config/clusters/cloudbank/enc-{hub_name}.secret.values.yaml` with the client ID and secret

**Output**: Should confirm "Successfully created a new CILogon client app" and "Successfully persisted the encrypted CILogon client app credentials"

---

### 4. Add Persistent Disk Entry to Terraform

Edit: `terraform/gcp/projects/cloudbank.tfvars`

Add entry in the `persistent_disks` map in **alphabetical order**:

```tfvars
  "{hub_name}" = {
    size        = {DISK_SIZE_GB}
    name_suffix = "{hub_name}"
  }
```

**Parameters:**
- `{DISK_SIZE_GB}`: Storage size in GB (e.g., `25` for small hubs, `60` for medium, `150+` for large)

**Example** (University of Chicago with 25GB disk, placed between `ucsc` and `unr`):
```tfvars
  "uchicago" = {
    size        = 25
    name_suffix = "uchicago"
  }
```

---

### 5. Provision Cloud Infrastructure with Terraform

Navigate to terraform directory and verify GCP project:

```bash
cd terraform/gcp
gcloud config get-value project  # Should show: cb-1003-1696
gcloud auth login # if needed
```

Initialize Terraform with backend configuration:

```bash
terraform init -backend-config=backends/cloudbank.hcl -reconfigure
```

Select the cloudbank workspace:

```bash
terraform workspace select cloudbank
```

Review the plan to verify only the new hub resources will be created:

```bash
terraform plan -var-file=projects/cloudbank.tfvars -lock=false > out.txt
cat out.txt | tail -50  # Review Changes to Outputs section
```

**Expected plan output:**
- `Plan: 3 to add, 0 to change, 0 to destroy`
- New resources: `google_compute_disk`, `google_compute_resource_policy`, `google_compute_disk_resource_policy_attachment`

Apply the changes:

```bash
terraform apply -var-file=projects/cloudbank.tfvars -lock=false
# Type 'yes' when prompted to confirm
```

Clean up:

```bash
rm out.txt  # Delete the plan output file
```

**Note**: Persistent disk creation takes ~2-5 minutes. The `-lock=false` flag may be needed if there's a state lock issue.

---

## Next Steps

After completing steps 1-5, commit and push all changes to GitHub:

```bash
git add config/clusters/cloudbank/{hub_name}.values.yaml
git add config/clusters/cloudbank/cluster.yaml
git add config/clusters/cloudbank/enc-{hub_name}.secret.values.yaml
git add terraform/gcp/projects/cloudbank.tfvars
git commit -m "Add {INSTITUTION_NAME} hub ({hub_name})"
git push origin main
```

Create a Pull Request on GitHub. The CI/CD pipeline will:
1. Validate the configuration
2. Deploy the hub to the cluster
3. Run health checks

Once the PR is merged, the hub will be live at `https://{hub_name}.cloudbank.2i2c.cloud`

---
