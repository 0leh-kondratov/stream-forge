# Минимальный Autopilot-кластер

resource "google_container_cluster" "autopilot" {
  name             = var.cluster_name
  location         = var.region
  enable_autopilot = true

  network    = google_compute_network.vpc.id
  subnetwork = google_compute_subnetwork.subnet.id

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  # проще удалять через Terraform
  deletion_protection = false

  # уменьшаем объём логов (только системные компоненты)
  logging_config {
    enable_components = ["SYSTEM_COMPONENTS"]
  }

  # ждём включения GKE API
  depends_on = [google_project_service.gke_api]
}
