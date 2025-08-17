data "template_file" "arango" {
  template = file("${path.module}/arango_deployment.yaml.tftpl")
  vars = {
    deployment_name = var.deployment_name
    namespace       = var.namespace
    mode            = var.mode
    arango_image    = var.arango_image
    storage_class   = var.storage_class
    storage_size    = var.storage_size
    root_secret_name= kubernetes_secret.root.metadata[0].name
  }
}

resource "kubectl_manifest" "arango" {
  yaml_body = data.template_file.arango.rendered
  wait      = true

  depends_on = [
    helm_release.arangodb_operator,
    kubernetes_secret.root
  ]
}
