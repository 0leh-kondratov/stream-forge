
resource "google_container_cluster" "autopilot_cluster" {
  project            = var.project_id
  name               = var.cluster_name
  location           = var.region
  enable_autopilot   = true
  network            = var.network_id
  subnetwork         = var.subnetwork_id
  networking_mode    = "VPC_NATIVE"

  ip_allocation_policy {
    cluster_secondary_range_name  = var.pods_cidr_range_name
    services_secondary_range_name = var.services_cidr_range_name
  }

  deletion_protection = false

  logging_config {
    enable_components = ["SYSTEM_COMPONENTS"]
  }

  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }
}
