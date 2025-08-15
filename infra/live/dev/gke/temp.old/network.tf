resource "google_compute_network" "vpc" {
  name                    = "gke-free-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.common_apis]
}

resource "google_compute_subnetwork" "subnet" {
  name          = "gke-free-subnet"
  region        = var.region
  network       = google_compute_network.vpc.id
  ip_cidr_range = var.vpc_cidr

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = var.pods_cidr
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = var.services_cidr
  }
}