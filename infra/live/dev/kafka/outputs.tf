output "kafka_namespace" {
  value = var.kafka_namespace
}

output "kafka_cluster_name" {
  value = var.kafka_cluster_name
}

output "internal_bootstrap_service" {
  value       = "${var.kafka_cluster_name}-kafka-bootstrap.${var.kafka_namespace}.svc.cluster.local:9092"
  description = "Внутренний bootstrap (ClusterIP)"
}

output "external_bootstrap_hint" {
  value = var.external_listener_enabled ? "kubectl -n ${var.kafka_namespace} get svc ${var.kafka_cluster_name}-kafka-external-bootstrap -o=jsonpath='{.status.loadBalancer.ingress[0].ip}{\"\\n\"}'" : ""
  description = "Команда получить внешний LB IP (если включен)"
}

output "kafka_user_secrets" {
  value = [
    for uname, _ in local.users_map :
    "${uname} -> secret: ${uname}"
  ]
  description = "Strimzi создаёт Secret с паролем SCRAM под тем же именем, что и KafkaUser."
}
