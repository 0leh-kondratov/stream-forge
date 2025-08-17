locals {
  arango_repo = "https://arangodb.github.io/kube-arangodb"
}

resource "helm_repository" "arangodb" {
  name = "arangodb"
  url  = local.arango_repo
}

# 1) CRDs — отдельный чарт
resource "helm_release" "arangodb_crd" {
  name       = "kube-arangodb-crd"
  repository = helm_repository.arangodb.url
  chart      = "kube-arangodb-crd"
  version    = var.crd_chart_version
  namespace  = var.namespace

  create_namespace = false
  wait             = true
  atomic           = true
  cleanup_on_fail  = true

  depends_on = [kubernetes_namespace.this]
}

# 2) Operator
resource "helm_release" "arangodb_operator" {
  name       = "kube-arangodb"
  repository = helm_repository.arangodb.url
  chart      = "kube-arangodb"
  version    = var.operator_chart_version
  namespace  = var.namespace

  create_namespace = false
  wait             = true
  atomic           = true
  cleanup_on_fail  = true

  # Пример полезных настройкок (можно расширять)
  values = [yamlencode({
    operator = {
      features = {
        # включённые операторы: deployment, storage, backup, replication
        deployment  = { enabled = true }
        storage     = { enabled = false } # в Autopilot чаще используем CSI PV, локальное хранилище не нужно
        backup      = { enabled = true }
        replication = { enabled = false }
      }
    }
  })]

  depends_on = [helm_release.arangodb_crd]
}
