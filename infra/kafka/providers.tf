# All comments in English
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.33"   # supports manifest resource
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.13"
    }
  }
}

provider "kubernetes" {
  config_path = var.kubeconfig
  # or host/token/cluster_ca_certificate if running in CI with a service account
}

provider "helm" {
  kubernetes {
    config_path = var.kubeconfig
  }
}
