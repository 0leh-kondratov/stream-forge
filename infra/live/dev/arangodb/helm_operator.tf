resource "helm_release" "arangodb_crd" {
  name       = "kube-arangodb-crd"
  repository = "https://arangodb.github.io/kube-arangodb"
  chart      = "kube-arangodb-crd"
  version    = var.crd_chart_version
  namespace  = var.namespace

  create_namespace = false
  wait             = true
  atomic           = true
  cleanup_on_fail  = true

  # 👇 добавь это
  depends_on = [kubernetes_namespace.this]
}

resource "helm_release" "arangodb_operator" {
  name       = "kube-arangodb"
  repository = "https://arangodb.github.io/kube-arangodb"
  chart      = "kube-arangodb"
  version    = var.operator_chart_version
  namespace  = var.namespace

  create_namespace = false
  wait             = true
  atomic           = true
  cleanup_on_fail  = true

  values = [yamlencode({
    operator = {
      features = {
        deployment  = { enabled = true }
        storage     = { enabled = false }
        backup      = { enabled = true }
        replication = { enabled = false }
      }
    }
  })]

  # 👇 и здесь тоже
  depends_on = [kubernetes_namespace.this, helm_release.arangodb_crd]
}
