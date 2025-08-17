locals {
  external_listener_block = var.external_listener_enabled ? {
    name = "external"
    port = 9094
    type = "loadbalancer"
    tls  = true
    authentication = {
      type = "scram-sha-512"
    }
    configuration = {
      bootstrap = {
        annotations = (
          var.external_lb_internal
          ? { "networking.gke.io/load-balancer-type" = "Internal" }
          : {}
        )
      }
    }
  } : null
}

# Kafka (включаем аннотации для NodePools+KRaft)
resource "kubernetes_manifest" "kafka" {
  manifest = yamldecode(<<-YAML
    apiVersion: kafka.strimzi.io/v1beta2
    kind: Kafka
    metadata:
      name: ${var.kafka_cluster_name}
      namespace: ${var.kafka_namespace}
      annotations:
        strimzi.io/kraft: "enabled"
        strimzi.io/node-pools: "enabled"
    spec:
      kafka:
        version: "${var.kafka_version}"
        authorization:
          type: simple
        listeners:
          - name: internal
            port: 9092
            type: internal
            tls: true
            authentication:
              type: scram-sha-512
          ${var.external_listener_enabled ? "" : "# external listener disabled"}
      entityOperator:
        topicOperator: {}
        userOperator: {}
  YAML
  )

  depends_on = [helm_release.strimzi_operator]
}

# KafkaNodePool: комбинированные роли controller+broker
resource "kubernetes_manifest" "kafka_nodepool_combined" {
  manifest = yamldecode(<<-YAML
    apiVersion: kafka.strimzi.io/v1beta2
    kind: KafkaNodePool
    metadata:
      name: combined
      namespace: ${var.kafka_namespace}
      labels:
        strimzi.io/cluster: ${var.kafka_cluster_name}
    spec:
      replicas: ${var.replicas_combined}
      roles:
        - controller
        - broker
      storage:
        type: persistent-claim
        size: ${var.storage_size}
        deleteClaim: false
        class: ${var.storage_class}
      resources:
        requests:
          cpu: "800m"
          memory: "4Gi"
        limits:
          cpu: "2"
          memory: "6Gi"
  YAML
  )

  depends_on = [kubernetes_manifest.kafka]
}

# Патч добавляющий внешний listener (если включен)
resource "kubernetes_manifest" "kafka_patch_external_listener" {
  count = var.external_listener_enabled ? 1 : 0

  manifest = yamldecode(<<-YAML
    apiVersion: kafka.strimzi.io/v1beta2
    kind: Kafka
    metadata:
      name: ${var.kafka_cluster_name}
      namespace: ${var.kafka_namespace}
    spec:
      kafka:
        listeners:
          - name: internal
            port: 9092
            type: internal
            tls: true
            authentication:
              type: scram-sha-512
          - name: external
            port: 9094
            type: loadbalancer
            tls: true
            authentication:
              type: scram-sha-512
            configuration:
              bootstrap:
                annotations:
                  ${var.external_lb_internal ? "networking.gke.io/load-balancer-type: \"Internal\"" : ""}
  YAML
  )

  depends_on = [
    kubernetes_manifest.kafka,
    kubernetes_manifest.kafka_nodepool_combined
  ]
}
