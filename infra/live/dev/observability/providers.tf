provider "google" {
  project = var.project_id
  region  = var.region
}

data "google_container_cluster" "gke" {
  name     = var.cluster
  location = var.region
}

data "google_client_config" "me" {}

provider "kubernetes" {
  host  = "https://${data.google_container_cluster.gke.endpoint}"
  token = data.google_client_config.me.access_token
  cluster_ca_certificate = base64decode(
    data.google_container_cluster.gke.master_auth[0].cluster_ca_certificate
  )
}

provider "helm" {
  kubernetes {
    host  = "https://${data.google_container_cluster.gke.endpoint}"
    token = data.google_client_config.me.access_token
    cluster_ca_certificate = base64decode(
      data.google_container_cluster.gke.master_auth[0].cluster_ca_certificate
    )
  }
}
