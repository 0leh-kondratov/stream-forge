
output "cluster_name" {
  description = "The name of the GKE cluster"
  value       = module.gke_cluster.name
}

output "cluster_region" {
  description = "The region of the GKE cluster"
  value       = module.gke_cluster.location
}

output "get_credentials_hint" {
  description = "Command to get kubeconfig for the cluster"
  value       = module.gke_cluster.get_credentials_hint
}
