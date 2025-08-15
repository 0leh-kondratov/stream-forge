variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "cluster_name" {
  description = "The name of the GKE cluster"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "network_id" {
  description = "The ID of the VPC network"
  type        = string
}

variable "subnetwork_id" {
  description = "The ID of the VPC subnetwork"
  type        = string
}

variable "pods_cidr_range_name" {
  description = "The name of the secondary IP range for pods"
  type        = string
  default     = "pods"
}

variable "services_cidr_range_name" {
  description = "The name of the secondary IP range for services"
  type        = string
  default     = "services"
}