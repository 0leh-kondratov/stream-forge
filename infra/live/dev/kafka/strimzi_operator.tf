resource "helm_release" "strimzi_operator" {
  name       = "strimzi-kafka-operator"
  repository = "https://strimzi.io/charts/"
  chart      = "strimzi-kafka-operator"
  version    = var.strimzi_chart_version
  namespace  = kubernetes_namespace_v1.operator_ns.metadata[0].name
  wait       = true
  timeout    = 600

  values = [yamlencode({
    # Следим только за namespace с Kafka (production-friendly)
    watchNamespaces    = [var.kafka_namespace]
    watchAnyNamespace  = false

    # Включаем фичи для KRaft + NodePools + Unidirectional Topic Operator
    extraEnvs = [
      {
        name  = "STRIMZI_FEATURE_GATES"
        value = "+KafkaNodePools,+UseKRaft,+UnidirectionalTopicOperator"
      }
    ]

    # Ресурсы для Autopilot
    resources = {
      requests = {
        cpu    = var.operator_resources.requests_cpu
        memory = var.operator_resources.requests_memory
      }
      limits = {
        cpu    = var.operator_resources.limits_cpu
        memory = var.operator_resources.limits_memory
      }
    }
  })]

  depends_on = [
    kubernetes_namespace_v1.operator_ns,
    kubernetes_namespace_v1.kafka_ns
  ]
}
