output "gsa_email" {
  value       = google_service_account.github_cicd.email
  description = "GCP Service Account email used by GitHub OIDC"
}

output "workload_identity_provider" {
  # Полный resource name провайдера (нужен в GitHub Secrets)
  value       = google_iam_workload_identity_pool_provider.github.name
  description = "projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/<POOL_ID>/providers/<PROVIDER_ID>"
}

output "artifact_registry_repo_url" {
  value       = "${var.gar_location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
  description = "Base URL for Artifact Registry Docker repo"
}