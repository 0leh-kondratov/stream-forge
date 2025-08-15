
module "gke_cluster" {
  source = "../../../modules/gke"

  project_id      = var.project_id
  cluster_name    = var.cluster_name
  region          = var.region
  network_id      = google_compute_network.vpc.id
  subnetwork_id   = google_compute_subnetwork.subnet.id
}

provider "kubernetes" {
  host                   = format("https://%s", module.gke_cluster.endpoint)
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(module.gke_cluster.ca_certificate)
}

data "google_client_config" "default" {}

resource "kubernetes_deployment" "nginx" {
  metadata {
    name = "nginx-deployment"
    labels = {
      app = "nginx"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "nginx"
      }
    }

    template {
      metadata {
        labels = {
          app = "nginx"
        }
      }

      spec {
        container {
          image = "nginx:1.14.2"
          name  = "nginx"

          port {
            container_port = 80
          }
        }
      }
    }
  }
}
