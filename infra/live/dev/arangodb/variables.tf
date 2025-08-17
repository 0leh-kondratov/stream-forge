variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "GKE region"
}

variable "cluster" {
  type        = string
  default     = "gke-free-autopilot"
  description = "GKE Autopilot cluster name"
}

variable "namespace" {
  type        = string
  default     = "arangodb"
  description = "Namespace for ArangoDB operator and DB"
}

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

variable "deployment_name" {
  type        = string
  default     = "arango-single"
  description = "ArangoDeployment name"
}

variable "mode" {
  type        = string
  default     = "Single"
  description = "Single | Cluster | ActiveFailover"
}

variable "storage_class" {
  type        = string
  default     = "standard-rwo"
  description = "StorageClass for PVC (GKE Autopilot default is standard-rwo)"
}

variable "storage_size" {
  type        = string
  default     = "20Gi"
  description = "PVC size for data"
}

variable "arango_image" {
  type        = string
  default     = "arangodb/arangodb:3.11"
  description = "ArangoDB image tag"
}

variable "root_password" {
  type        = string
  sensitive   = true
  description = "Root password for ArangoDB (stored in Secret)"
}
