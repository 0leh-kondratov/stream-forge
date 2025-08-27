# Quick Guide to Setting Up GitHub Actions with Workload Identity

You **do not need** to create a temporary credentials file. We have configured Workload Identity Federation, which allows your GitHub Actions pipeline to securely authenticate to Google Cloud without long-lived keys.

### How to use it:

**1. Configure GitHub Secrets:**

*   In your GitHub repository settings, go to `Settings` > `Secrets and variables` > `Actions`.
*   Create two secrets:
    *   `GCP_WORKLOAD_IDENTITY_PROVIDER`: copy the value from the `workload_identity_provider` Terraform output.
    *   `GCP_SERVICE_ACCOUNT`: copy the value from the `gsa_email` Terraform output.

**2. Use `google-github-actions/auth` in your workflow:**

*   In your `.github/workflows/main.yml` file (or any other), add the following step to authenticate:

```yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
    service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}
```

After this step, all subsequent commands in your pipeline (e.g., `gcloud`, `gsutil`, `docker push` to Artifact Registry) will be authenticated as the service account we created.

### About `.gitignore`:

Since a credentials file is not needed, you do not need to add it to `.gitignore`. However, if other temporary files are created during the pipeline's execution, they should be added to `.gitignore`.

artifact_registry_repo_url = "europe-central2-docker.pkg.dev/stream-forge-4/apps"
gsa_email = "github-cicd@stream-forge-4.iam.gserviceaccount.com"
workload_identity_provider = "projects/635346433944/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
