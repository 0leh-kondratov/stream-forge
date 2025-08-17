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
variable "replicas"   { type = number }
variable "kafka_version_str"    { type = string }

locals {
  rendered = replace(
    replace(
      replace(
        file("${path.module}/kafka.yaml"),
        "{{KAFKA_NAME}}", var.kafka_name
      ),
      "{{NAMESPACE}}", var.namespace
    ),
    "{{KAFKA_VERSION}}", var.kafka_version_str
  )
  rendered2 = replace(local.rendered, "{{REPLICAS}}", tostring(var.replicas))
}

data "kubectl_file_documents" "kafka" {
  content = local.rendered2
}

resource "kubectl_manifest" "kafka" {
  for_each  = data.kubectl_file_documents.kafka.manifests
  yaml_body = each.value
  wait      = true
}
