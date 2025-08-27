terraform {
  required_version = ">= 1.6"
}

# --- GKE / общий ввод ---
variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "GKE region (cluster location)"
}

# ⚠️ Используем именно cluster_name (совпадает с terraform.tfvars)
variable "cluster_name" {
  type        = string
  default     = "gke-free-autopilot"
  description = "GKE Autopilot cluster name"
}

variable "namespace" {
  type        = string
  default     = "arangodb"
  description = "Namespace for ArangoDB operator and DB"
}

# --- ArangoDB настройки ---
variable "deployment_name" {
  type        = string
  default     = "arango-single"
  description = "ArangoDeployment name"
}

# Single | Cluster | ActiveFailover
variable "mode" {
  type        = string
  default     = "Single"
  description = "ArangoDB mode"
}

variable "storage_class" {
  type        = string
  default     = "standard-rwo"
  description = "StorageClass for PVC (GKE Autopilot default)"
}

variable "storage_size" {
  type        = string
  default     = "20Gi"
  description = "PVC size for data"
}

variable "arango_image" {
  type        = string
  default     = "arangodb/arangodb:3.11"
  description = "ArangoDB image"
}

# --- Helm chart versions (фиксируем для воспроизводимости) ---
variable "operator_chart_version" {
  type        = string
  default     = "1.2.31"
  description = "Helm chart version for kube-arangodb"
}

variable "crd_chart_version" {
  type        = string
  default     = "1.2.31"
  description = "Helm chart version for kube-arangodb-crd"
}

# --- Секреты ---
variable "root_password" {
  type        = string
  sensitive   = true
  description = "Root password (stored in Secret)"
}
