# Отдельный namespace для Strimzi и всех CR
resource "kubernetes_namespace_v1" "kafka" {
  metadata {
    name = "kafka"
    labels = {
      "name" = "kafka"
    }
  }
}
