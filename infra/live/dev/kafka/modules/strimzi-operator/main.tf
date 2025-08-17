variable "namespace" {
  type    = string
  default = "kafka"
}

resource "kubernetes_namespace" "ns" {
  metadata { name = var.namespace }
}

resource "helm_release" "strimzi" {
  name       = "strimzi-kafka-operator"
  repository = "https://strimzi.io/charts/"
  chart      = "strimzi-kafka-operator"
  version    = "0.41.0" # при необходимости обновите
  namespace  = var.namespace

  set {
    name  = "installCRDs"
    value = "true"
  }

  wait          = true
  timeout       = 600
  recreate_pods = true

  depends_on = [kubernetes_namespace.ns]
}
