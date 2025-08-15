variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "cluster" {
  type    = string
  default = "gke-free-autopilot"
}

variable "grafana_admin_password" {
  type      = string
  sensitive = true
  default   = "change_me"
}
