output "name" {
  description = "Cluster name"
  value       = google_container_cluster.autopilot_cluster.name
}

output "location" {
  description = "Cluster location (region)"
  value       = google_container_cluster.autopilot_cluster.location
}

output "endpoint" {
  description = "GKE API endpoint"
  value       = google_container_cluster.autopilot_cluster.endpoint
}

output "ca_certificate" {
  description = "Cluster CA certificate"
  value       = google_container_cluster.autopilot_cluster.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "workload_identity_pool" {
  description = "Workload Identity pool (for KSA->GSA bindings)"
  value       = try(google_container_cluster.autopilot_cluster.workload_identity_config[0].workload_pool, null)
}

output "get_credentials_hint" {
  description = "Convenience command to update kubeconfig"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.autopilot_cluster.name} --region ${var.region} --project ${var.project_id}"
}
