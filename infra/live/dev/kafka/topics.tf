locals {
  topics_map = {
    for t in var.kafka_topics :
    t.name => t
  }
}

resource "kubernetes_manifest" "topics" {
  for_each = local.topics_map

  manifest = {
    apiVersion = "kafka.strimzi.io/v1beta2"
    kind       = "KafkaTopic"
    metadata = {
      name      = each.value.name
      namespace = var.kafka_namespace
      labels = {
        "strimzi.io/cluster" = var.kafka_cluster_name
      }
    }
    spec = {
      partitions        = each.value.partitions
      replicas          = each.value.replication_factor
      config = {
        "retention.ms"          = "604800000" # 7d
        "segment.bytes"         = "1073741824"
        "min.insync.replicas"   = 2
        "cleanup.policy"        = "delete"
      }
    }
  }

  depends_on = [
    kubernetes_manifest.kafka_nodepool_combined
  ]
}
