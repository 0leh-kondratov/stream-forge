provider "google" {
  project = var.project_id
  region  = var.region
}

# Токен текущего аккаунта gcloud
data "google_client_config" "default" {}

# Данные о существующем GKE Autopilot кластере
data "google_container_cluster" "cluster" {
  name     = var.cluster
  location = var.region
}

# Инициализация kubernetes-провайдера по данным кластера
provider "kubernetes" {
  host                   = "https://${data.google_container_cluster.cluster.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(data.google_container_cluster.cluster.master_auth[0].cluster_ca_certificate)
}

# Helm использует те же креды/endpoint
provider "helm" {
  kubernetes {
    host                   = "https://${data.google_container_cluster.cluster.endpoint}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(data.google_container_cluster.cluster.master_auth[0].cluster_ca_certificate)
  }
}
