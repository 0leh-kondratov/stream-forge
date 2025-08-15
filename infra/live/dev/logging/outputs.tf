output "kibana_port_forward" {
  description = "Проброс Kibana (локально на 5601)"
  value       = "kubectl -n logging port-forward svc/kibana-kibana 5601:5601"
}

output "es_port_forward" {
  description = "Проброс Elasticsearch (локально на 9200)"
  value       = "kubectl -n logging port-forward svc/elasticsearch-master 9200:9200"
}

output "es_curl_tip" {
  description = "Проверка доступности ES (dev, без security)"
  value       = "curl http://localhost:9200"
}
