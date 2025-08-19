variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "europe-central2"
  description = "регион GCP"
}

variable "gke_location" {
  type = string
  description = "регион или зона кластера (например, \"europe-central2\")"
}

variable "cluster_name" {
  type = string
  description = "имя GKE кластера"
}

# GitHub OIDC ограничения
variable "github_repo" {
  type = string
  description = "\"owner/repo\", напр. \"0leh-kondratov/stream-forge\""
}

variable "github_ref" {
  type    = string
  default = "refs/heads/main"
  description = "ветка/тег"
}

# Artifact Registry
variable "gar_location" {
  type    = string
  default = "europe-central2"
}

variable "gar_repo_name" {
  type    = string
  default = "apps"
}

# Kubernetes namespace для деплоя
variable "k8s_namespace" {
  type    = string
  default = "default"
}

variable "vpc_cidr" {
  description = "The CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "pods_cidr" {
  description = "The CIDR block for pods"
  type        = string
  default     = "10.1.0.0/16"
}

variable "services_cidr" {
  description = "The CIDR block for services"
  type        = string
  default     = "10.2.0.0/20"
}
