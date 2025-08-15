variable "project_id" {
  type        = string
  description = <<-EOT
  Google Cloud project ID.
  EOT
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = <<-EOT
  GKE region (для Autopilot или регионального кластера). Используется как
  значение data.google_container_cluster.location.
  EOT
}

variable "cluster" {
  type        = string
  default     = "gke-free-autopilot"
  description = <<-EOT
  Имя существующего GKE Autopilot кластера.
  EOT
}
