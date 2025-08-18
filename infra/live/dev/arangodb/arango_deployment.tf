# Рендерим CR ArangoDeployment из шаблона
locals {
  arango_yaml = templatefile("${path.module}/arango_deployment.yaml.tftpl", {
    deployment_name  = var.deployment_name
    namespace        = var.namespace
    mode             = var.mode
    arango_image     = var.arango_image
    storage_class    = var.storage_class
    storage_size     = var.storage_size
    root_secret_name = kubernetes_secret.root.metadata[0].name
  })
}

resource "kubectl_manifest" "arango" {
  yaml_body = local.arango_yaml
  wait      = true

  depends_on = [
    kubernetes_namespace.this,
    helm_release.arangodb_operator,
    kubernetes_secret.root
  ]
}

