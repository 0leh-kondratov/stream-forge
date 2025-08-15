variable "project_id" {
  type        = string
  description = <<-EOT
    GCP Project ID, в котором уже существует Autopilot-кластер GKE.
    Пример: "my-gcp-project".
  EOT
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = <<-EOT
    Регион GKE кластера (location). Для Autopilot Free по умолчанию "us-central1".
  EOT
}

variable "cluster" {
  type        = string
  default     = "gke-free-autopilot"
  description = <<-EOT
    Имя существующего GKE Autopilot кластера. Кластер должен уже существовать.
  EOT
}

# --- Пути к вашим PEM-файлам для кастомных CA (Вариант A) ---

variable "cluster_ca_crt_path" {
  type        = string
  description = <<-EOT
    Путь к PEM файлу сертификата Cluster CA (например: ./certs/clusterCA.crt).
  EOT
}

variable "cluster_ca_key_path" {
  type        = string
  sensitive   = true
  description = <<-EOT
    Путь к PEM файлу приватного ключа Cluster CA (например: ./certs/clusterCA.key).
  EOT
}

variable "clients_ca_crt_path" {
  type        = string
  description = <<-EOT
    Путь к PEM файлу сертификата Clients CA (например: ./certs/clientsCA.crt).
  EOT
}

variable "clients_ca_key_path" {
  type        = string
  sensitive   = true
  description = <<-EOT
    Путь к PEM файлу приватного ключа Clients CA (например: ./certs/clientsCA.key).
  EOT
}
