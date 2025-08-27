variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "GKE region"
}

variable "cluster_name" {
  type        = string
  default     = "gke-free-autopilot"
  description = "Existing GKE Autopilot cluster name"
}

variable "observability_namespace" {
  type        = string
  default     = "observability"
  description = "Namespace for Alloy"
}

# Установить ли kube-state-metrics (рекомендую true — для K8s метрик)
variable "install_kube_state_metrics" {
  type        = bool
  default     = true
  description = "Install kube-state-metrics for richer Kubernetes metrics"
}

# === Grafana Cloud (Prometheus / Mimir) ===
variable "grafana_cloud_prometheus_remote_write_endpoint" {
  type        = string
  description = "Base remote_write endpoint, e.g. https://prometheus-prod-XX.grafana.net/api/prom"
}
variable "grafana_cloud_prometheus_user" {
  type        = string
  description = "Metrics instance ID / username"
}
variable "grafana_cloud_prometheus_api_key" {
  type        = string
  description = "Access policy token with metrics:write"
  sensitive   = true
}

# === Grafana Cloud (Loki) ===
variable "grafana_cloud_loki_endpoint" {
  type        = string
  description = "Base Loki endpoint, e.g. https://logs-prod-XXX.grafana.net"
}
variable "grafana_cloud_loki_user" {
  type        = string
  description = "Loki user/tenant id"
}
variable "grafana_cloud_loki_api_key" {
  type        = string
  description = "Access policy token with logs:write"
  sensitive   = true
}

# === (Optional) Tempo / OTLP traces (по умолчанию отключено) ===
variable "grafana_tempo_otlp_endpoint" {
  type        = string
  description = "OTLP endpoint, e.g. https://tempo-prod-<region>.grafana.net:443; empty to disable traces"
  default     = ""
}
variable "grafana_tempo_token" {
  type        = string
  description = "Access policy token with traces:write"
  sensitive   = true
  default     = ""
}
