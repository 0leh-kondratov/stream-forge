resource "kubernetes_secret" "root" {
  metadata {
    name      = "${var.deployment_name}-root"
    namespace = var.namespace
  }
  data = {
    username = base64encode("root")
    password = base64encode(var.root_password)
  }
  type = "Opaque"
}
