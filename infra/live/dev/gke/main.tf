module "gke_cluster" {
  source = "../../../modules/gke"

  project_id      = var.project_id
  cluster_name    = var.cluster_name
  region          = var.region
  network_id      = google_compute_network.vpc.id
  subnetwork_id   = google_compute_subnetwork.subnet.id
}
