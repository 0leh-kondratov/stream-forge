provider "google" {
  project = var.project_id
  region  = var.region
}

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 6.0" }
    kubernetes = { source = "hashicorp/kubernetes", version = "~> 2.31" }
  }
}

data "google_client_config" "default" {}

provider "kubernetes" {
  host                   = format("https://%s", module.gke_cluster.endpoint)
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(module.gke_cluster.ca_certificate)
}
