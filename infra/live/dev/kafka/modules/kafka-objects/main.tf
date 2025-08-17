terraform {
  required_providers {
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = "~> 1.14"
    }
  }
}

variable "namespace"  { type = string }
variable "kafka_name" { type = string }

locals {
  rendered = replace(
    replace(
      file("${path.module}/objects.yaml"),
      "{{NAMESPACE}}", var.namespace
    ),
    "{{KAFKA_NAME}}", var.kafka_name
  )
}

data "kubectl_file_documents" "objs" {
  content = local.rendered
}

resource "kubectl_manifest" "objs" {
  for_each  = data.kubectl_file_documents.objs.manifests
  yaml_body = each.value
  wait      = true
}
