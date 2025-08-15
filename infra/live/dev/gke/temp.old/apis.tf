# Включаем API до ресурсов
locals {
  common_apis = [
    "serviceusage.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "iam.googleapis.com",
  ]
}

resource "google_project_service" "gke_api" {
  project            = var.project_id
  service            = "container.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "common_apis" {
  for_each           = toset(local.common_apis)
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}
