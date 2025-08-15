
output "cluster_name" {
  description = "The name of the GKE cluster"
  value       = google_container_cluster.autopilot_cluster.name
}

output "cluster_region" {
  description = "The region of the GKE cluster"
  value       = var.region
}

output "get_credentials_hint" {
  description = "Command to get kubeconfig for the cluster"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.autopilot_cluster.name} --region ${var.region} --project ${var.project_id}"
}

output "endpoint" {
  description = "The endpoint of the GKE cluster"
  value       = google_container_cluster.autopilot_cluster.endpoint
}

output "ca_certificate" {
  description = "The CA certificate of the GKE cluster"
  value       = google_container_cluster.autopilot_cluster.master_auth[0].cluster_ca_certificate
}
