resource "kubernetes_namespace_v1" "operator_ns" {
  metadata { name = var.operator_namespace }
}

resource "kubernetes_namespace_v1" "kafka_ns" {
  metadata { name = var.kafka_namespace }
}
