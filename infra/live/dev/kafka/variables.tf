variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GKE region (например, us-central1)"
  type        = string
  default     = "us-central1"
}

variable "cluster_name" {
  description = "Имя существующего GKE Autopilot кластера"
  type        = string
  default     = "gke-free-autopilot"
}

variable "strimzi_chart_version" {
  description = "Версия Helm-чарта Strimzi"
  type        = string
  default     = "0.47.0"
}

variable "operator_namespace" {
  description = "Namespace для Strimzi Cluster Operator"
  type        = string
  default     = "strimzi-system"
}

variable "kafka_namespace" {
  description = "Namespace для Kafka кластера"
  type        = string
  default     = "kafka"
}

variable "kafka_cluster_name" {
  description = "Имя Kafka кластера (CR metadata.name)"
  type        = string
  default     = "streamforge-kafka"
}

variable "kafka_version" {
  description = "Версия Apache Kafka, поддерживаемая Strimzi"
  type        = string
  default     = "3.7.0"
}

variable "replicas_combined" {
  description = "Число узлов в комбинированном KRaft-пуле (controller+broker)"
  type        = number
  default     = 3
}

variable "storage_class" {
  description = "StorageClass для данных брокеров"
  type        = string
  default     = "standard-rwo"
}

variable "storage_size" {
  description = "Размер PVC на брокер"
  type        = string
  default     = "100Gi"
}

variable "external_listener_enabled" {
  description = "Включить внешний listener (LoadBalancer)"
  type        = bool
  default     = true
}

variable "external_lb_internal" {
  description = "Делать внешний LoadBalancer внутренним (ILB) в VPC"
  type        = bool
  default     = true
}

variable "kafka_topics" {
  description = "Список тестовых топиков (name, partitions, replicationFactor)"
  type = list(object({
    name               = string
    partitions         = number
    replication_factor = number
  }))
  default = [
    { name = "queue-control", partitions = 3, replication_factor = 3 },
    { name = "queue-events",  partitions = 3, replication_factor = 3 }
  ]
}

variable "kafka_users" {
  description = "Список KafkaUser (SCRAM-SHA-512). Поля: name и optional acls"
  type = list(object({
    name = string
    acls = optional(list(object({
      resource_type = string # topic | group | cluster | transactionalId
      name          = string
      pattern_type  = optional(string, "literal")
      operation     = string  # Read | Write | Create | Delete | Alter | All ...
      host          = optional(string, "*")
    })), [])
  }))
  default = [
    { name = "user-streamforge" }
  ]
}

variable "operator_resources" {
  description = "Requests/Limits для Strimzi operator (Autopilot требует ресурсы)"
  type = object({
    requests_cpu    = string
    requests_memory = string
    limits_cpu      = string
    limits_memory   = string
  })
  default = {
    requests_cpu    = "200m"
    requests_memory = "256Mi"
    limits_cpu      = "500m"
    limits_memory   = "512Mi"
  }
}
