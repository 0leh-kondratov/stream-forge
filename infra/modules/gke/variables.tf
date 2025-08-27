variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "Region where the Autopilot cluster will be created"
  type        = string
}

variable "cluster_name" {
  description = "Name of the GKE Autopilot cluster"
  type        = string
}

variable "network_id" {
  description = "Self link or name of the VPC network to use"
  type        = string
}

variable "subnetwork_id" {
  description = "Self link or name of the subnetwork to use"
  type        = string
}

variable "release_channel" {
  description = "GKE release channel (RAPID, REGULAR, STABLE)"
  type        = string
  default     = "REGULAR"

  validation {
    condition     = contains(["RAPID", "REGULAR", "STABLE"], var.release_channel)
    error_message = "release_channel must be RAPID, REGULAR, or STABLE."
  }
}

variable "labels" {
  description = "Common resource labels (e.g., { env = \"dev\", team = \"platform\" })"
  type        = map(string)
  default     = {}
}

# Опционально: если заранее созданы secondary ranges в сабнете — укажите их имена.
# Если оставить null, блок ip_allocation_policy не будет задан (Autopilot настроит сам).
variable "pods_cidr_range_name" {
  description = "Secondary range name for Pods (optional)"
  type        = string
  default     = null
}

variable "services_cidr_range_name" {
  description = "Secondary range name for Services (optional)"
  type        = string
  default     = null
}
