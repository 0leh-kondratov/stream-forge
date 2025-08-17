terraform {
  required_providers {
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = "~> 1.14"
    }
  }
}

variable "namespace"         { type = string }
variable "kafka_name"        { type = string }
variable "replicas"          { type = number }
variable "kafka_version_str" { type = string } # напр. "4.0.0"

# Если нужно, вынеси storage class в переменную:
# variable "storage_class" { type = string, default = "standard-rwo" }

locals {
  # Рендер плейсхолдеров
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
  # Если захотите параметризовать storage class:
  # rendered2 = replace(local.rendered, "{{STORAGE_CLASS}}", var.storage_class)
}

# Разбиваем много-документный YAML
data "kubectl_file_documents" "docs" {
  content = local.rendered2
}

# Декодируем, чтобы получить kind/name и сделать стабильные ключи
locals {
  docs_decoded = [for d in data.kubectl_file_documents.docs.documents : yamldecode(d)]
  docs_map = {
    for d in local.docs_decoded :
    "${d.kind}.${lookup(d, "metadata", {})["name"]}" => d
  }
}

# Применяем каждый документ отдельно
resource "kubectl_manifest" "this" {
  for_each  = local.docs_map
  yaml_body = yamlencode(each.value)
  wait      = true
}

