terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google     = { source = "hashicorp/google",     version = "~> 6.48" }
    kubernetes = { source = "hashicorp/kubernetes", version = "~> 2.31" }
    helm       = { source = "hashicorp/helm",       version = "~> 3.0" }
    kubectl    = { source = "gavinbunney/kubectl",  version = "~> 1.19" }
    time       = { source = "hashicorp/time",       version = "~> 0.11" }
    null       = { source = "hashicorp/null",       version = "~> 3.2" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

data "google_container_cluster" "gke" {
  project  = var.project_id
  name     = var.cluster_name
  location = var.region
}

data "google_client_config" "default" {}

# kubernetes-провайдер — без изменений (v2.x)
provider "kubernetes" {
  alias          = "ctx"
  config_path    = pathexpand("~/.kube/config")
  config_context = "gke_${var.project_id}_${var.region}_${var.cluster_name}"
}

# helm v3 — kubernetes как ОДИН аргумент-объект, а не блок
provider "helm" {
  alias = "ctx"
  kubernetes = {
    config_path    = pathexpand("~/.kube/config")
    config_context = "gke_${var.project_id}_${var.region}_${var.cluster_name}"
  }
}
