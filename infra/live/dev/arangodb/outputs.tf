output "namespace" {
  value = var.namespace
}

output "arango_deployment_name" {
  value = var.deployment_name
}

output "kubectl_status_hint" {
  value = "kubectl -n ${var.namespace} get arango,po,svc,pvc"
}

output "port_forward_hint" {
  value = "kubectl -n ${var.namespace} port-forward svc/${var.deployment_name} 8529:8529"
}
