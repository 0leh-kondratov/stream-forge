resource "google_container_cluster" "autopilot_cluster" {
  project          = var.project_id
  name             = var.cluster_name
  location         = var.region
  enable_autopilot = true
  deletion_protection = true

  # Важно: Autopilot — VPC-native. Можно указать имена secondary ranges (опционально ниже).
  network    = var.network_id
  subnetwork = var.subnetwork_id

  # Если заранее существуют secondary ranges — задайте их; иначе блок будет опущен.
  dynamic "ip_allocation_policy" {
    for_each = (var.pods_cidr_range_name != null && var.services_cidr_range_name != null) ? [1] : []
    content {
      cluster_secondary_range_name  = var.pods_cidr_range_name
      services_secondary_range_name = var.services_cidr_range_name
    }
  }

  # Канал обновлений кластера
  release_channel {
    channel = var.release_channel
  }

  # === ЛОГИ ===
  # Критично: включаем сбор логов не только системных компонентов, но и WORKLOADS (подов приложений)
  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }

  # === МЕТРИКИ ===
  # Managed Service for Prometheus (GMP) — включён, чтобы собирать Prometheus-метрики приложений.
  # Компонентные метрики системы также включены.
  monitoring_config {
    managed_prometheus {
      enabled = true
    }

    # Безопасный набор компонентов (поддерживается в актуальных версиях API/провайдера).
    enable_components = [
      "SYSTEM_COMPONENTS",
      "APISERVER",
      "SCHEDULER",
      "CONTROLLER_MANAGER",
      "STORAGE"
    ]
  }

  # Рекомендуемое: не выпускать клиентские сертификаты
  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }

  # Метки для кластера
  resource_labels = var.labels

  # Autopilot сам управляет нодами; node_config/node_pool здесь отсутствуют
}

# Удобные data-ресурсы для провайдера kubernetes вне модуля
data "google_container_cluster" "this" {
  project  = var.project_id
  name     = google_container_cluster.autopilot_cluster.name
  location = var.region
}

data "google_client_config" "default" {}
