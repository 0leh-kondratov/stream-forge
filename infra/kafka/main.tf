# 1) Namespace (idempotent)
resource "kubernetes_namespace" "kafka" {
  metadata {
    name = var.namespace
    labels = {
      "app.kubernetes.io/part-of" = "streamforge"
    }
  }
}

# 2) Helm release: Strimzi Operator
resource "helm_release" "strimzi" {
  name       = "strimzi-operator"
  repository = "https://strimzi.io/charts/"
  chart      = "strimzi-kafka-operator"
  namespace  = kubernetes_namespace.kafka.metadata[0].name
  version    = "0.46.0" # align with your cluster

  values = [
    file("${path.module}/values/strimzi-operator-values.yaml")
  ]
}

# 3) Kafka cluster CR (rendered from template)
locals {
  kafka_yaml = templatefile("${path.module}/templates/k3-kafka.yaml.tmpl", {
    namespace      = var.namespace
    cluster_name   = var.cluster_name
    storage_class  = var.storage_class
    kafka_replicas = var.kafka_replicas
    zk_replicas    = var.zk_replicas
    ingress_class  = var.ingress_class
    bootstrap_host = var.bootstrap_host
    broker_hosts   = var.broker_hosts
  })
}

resource "kubernetes_manifest" "kafka_cluster" {
  manifest = yamldecode(local.kafka_yaml)
  depends_on = [helm_release.strimzi]
}

# 4) Topics (iterate)
locals {
  topics_yaml = [for t in var.topics : templatefile("${path.module}/templates/k3-topics.yaml.tmpl", {
    namespace     = var.namespace
    cluster_name  = var.cluster_name
    topic_name    = t.name
    partitions    = t.partitions
    replicas      = t.replicas
    retention_ms  = t.retention_ms
    cleanup_policy= t.cleanup_policy
  })]
}

resource "kubernetes_manifest" "topics" {
  for_each = { for idx, y in local.topics_yaml : idx => yamldecode(y) }
  manifest = each.value
  depends_on = [kubernetes_manifest.kafka_cluster]
}

# 5) User (optional)
locals {
  user_yaml = templatefile("${path.module}/templates/k3-user-streamforge.yaml.tmpl", {
    namespace    = var.namespace
    cluster_name = var.cluster_name
  })
}

resource "kubernetes_manifest" "user_streamforge" {
  count    = var.create_user_streamforge ? 1 : 0
  manifest = yamldecode(local.user_yaml)
  depends_on = [kubernetes_manifest.kafka_cluster]
}

# 6) Output: SCRAM password and CA cert (names only; fetch in CI/kubectl as needed)
output "user_streamforge_secret_name" {
  description = "Secret name with SCRAM password"
  value       = var.create_user_streamforge ? "user-streamforge" : null
}

output "cluster_ca_secret_name" {
  description = "Secret name with cluster CA certificate"
  value       = "${var.cluster_name}-cluster-ca-cert"
}
