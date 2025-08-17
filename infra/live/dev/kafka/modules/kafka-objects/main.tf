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

# 🔹 Разбираем много-документный YAML на список отдельных документов
data "kubectl_file_documents" "objs" {
  content = local.rendered
}

# 🔹 Создаём kubectl_manifest для каждого документа
resource "kubectl_manifest" "objs" {
  count     = length(data.kubectl_file_documents.objs.documents)
  yaml_body = data.kubectl_file_documents.objs.documents[count.index]
  wait      = true
}
