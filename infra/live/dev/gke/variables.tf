variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GKE region (Autopilot кластеры региональные)"
  type        = string
  default     = "us-central1"
}

variable "cluster_name" {
  description = "Имя кластера (делай уникальным, если создаёшь второй)"
  type        = string
  default     = "gke-free-autopilot"
}

# Сети — можно не трогать
variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "Primary CIDR для сабнета"
}

variable "pods_cidr" {
  type    = string
  default = "10.1.0.0/16"
}

variable "services_cidr" {
  type    = string
  default = "10.2.0.0/20"
}
