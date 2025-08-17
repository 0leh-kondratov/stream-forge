output "observability_namespace" {
  value = var.observability_namespace
}

output "notes" {
  value = <<EOT
Alloy (manual config) deployed to '${var.observability_namespace}'.
Check Grafana Cloud → Explore:
- Prometheus: topk(5, up), label_values(up, cluster)
- Loki: {cluster="${var.cluster_name}"}
EOT
}
