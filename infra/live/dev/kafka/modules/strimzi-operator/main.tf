variable "namespace" {
  type    = string
  default = "kafka"
}

resource "kubernetes_namespace" "ns" {
  metadata { name = var.namespace }
}

resource "helm_release" "strimzi" {
  name       = "strimzi-kafka-operator"
  repository = "oci://quay.io/strimzi-helm"
  chart      = "strimzi-kafka-operator"
  version    = "0.47.0"
  namespace  = var.namespace

  wait            = true
  atomic          = true
  cleanup_on_fail = true
  timeout         = 900

  # Если нужны какие-то values — используйте values или set-список.
  # Пример ограничения оператором наблюдаемого неймспейса:
  # values = [yamlencode({ watchNamespaces = [var.namespace] })]

  depends_on = [kubernetes_namespace.ns]
}

