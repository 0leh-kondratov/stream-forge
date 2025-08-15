output "grafana_port_forward" {
  value = "kubectl -n observability port-forward svc/kps-grafana 3000:80"
}

output "grafana_password_hint" {
  value     = "admin / ${var.grafana_admin_password}"
  sensitive = true
}
