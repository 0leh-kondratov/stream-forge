resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.gar_location
  repository_id = var.gar_repo_name
  description   = "Application Docker images"
  format        = "DOCKER"
}