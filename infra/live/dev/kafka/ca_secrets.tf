# ===== Кастомные CA для Strimzi (Вариант A): создаём ДО Kafka CR =====

# Cluster CA: приватный ключ + сертификат
resource "kubernetes_secret_v1" "dev_kafka_cluster_ca" {
  metadata {
    name      = "dev-kafka-cluster-ca"
    namespace = kubernetes_namespace_v1.kafka.metadata[0].name
  }
  data = {
    "ca.crt" = file(var.cluster_ca_crt_path)
    "ca.key" = file(var.cluster_ca_key_path)
  }
  type = "Opaque"
}

# Cluster CA public chain (Strimzi читает ca.crt)
resource "kubernetes_secret_v1" "dev_kafka_cluster_ca_cert" {
  metadata {
    name      = "dev-kafka-cluster-ca-cert"
    namespace = kubernetes_namespace_v1.kafka.metadata[0].name
  }
  data = {
    "ca.crt" = file(var.cluster_ca_crt_path)
  }
  type = "Opaque"
}

# Clients CA: приватный ключ + сертификат (для клиентских сертификатов при mTLS)
resource "kubernetes_secret_v1" "dev_kafka_clients_ca" {
  metadata {
    name      = "dev-kafka-clients-ca"
    namespace = kubernetes_namespace_v1.kafka.metadata[0].name
  }
  data = {
    "ca.crt" = file(var.clients_ca_crt_path)
    "ca.key" = file(var.clients_ca_key_path)
  }
  type = "Opaque"
}

# Clients CA public chain
resource "kubernetes_secret_v1" "dev_kafka_clients_ca_cert" {
  metadata {
    name      = "dev-kafka-clients-ca-cert"
    namespace = kubernetes_namespace_v1.kafka.metadata[0].name
  }
  data = {
    "ca.crt" = file(var.clients_ca_crt_path)
  }
  type = "Opaque"
}
