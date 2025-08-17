locals {
  users_map = {
    for u in var.kafka_users :
    u.name => u
  }
}

resource "kubernetes_manifest" "users" {
  for_each = local.users_map

  manifest = {
    apiVersion = "kafka.strimzi.io/v1beta2"
    kind       = "KafkaUser"
    metadata = {
      name      = each.value.name
      namespace = var.kafka_namespace
      labels = {
        "strimzi.io/cluster" = var.kafka_cluster_name
      }
    }
    spec = {
      authentication = {
        type = "scram-sha-512"
      }
      authorization = {
        acls = (
          length(lookup(each.value, "acls", [])) > 0
          ? [
              for a in each.value.acls : {
                resource = {
                  type        = a.resource_type
                  name        = a.name
                  patternType = lookup(a, "pattern_type", "literal")
                }
                operation = a.operation
                host      = lookup(a, "host", "*")
              }
            ]
          : [
              # Разрешим чтение/запись всех топиков и групп по умолчанию (dev)
              {
                resource  = { type = "topic", name = "*", patternType = "literal" }
                operation = "All"
                host      = "*"
              },
              {
                resource  = { type = "group", name = "*", patternType = "literal" }
                operation = "All"
                host      = "*"
              }
            ]
        )
      }
    }
  }

  depends_on = [
    kubernetes_manifest.kafka_nodepool_combined
  ]
}
