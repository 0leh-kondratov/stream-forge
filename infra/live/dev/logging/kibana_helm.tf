resource "helm_release" "kibana" {
  name             = "kibana"
  repository       = "https://helm.elastic.co"
  chart            = "kibana"
  version          = "8.5.1" # зафиксированная стабильная версия
  namespace        = kubernetes_namespace_v1.logging.metadata[0].name
  create_namespace = false

  # В чарте Kibana ключ для адреса ES — elasticsearchHosts (см. шаблоны Kibana чарта).
  values = [<<-YAML
    service:
      type: ClusterIP

    resources:
      requests:
        cpu: "100m"
        memory: "256Mi"

    elasticsearchHosts: "http://elasticsearch-master.logging.svc:9200"

    # Это минимальная dev-конфигурация. Не используйте в проде.
    # Пример для Spot (закомментировано):
    # nodeSelector:
    #   cloud.google.com/gke-spot: "true"
  YAML
  ]

  wait            = true
  timeout         = 600
  atomic          = true
  cleanup_on_fail = true

  depends_on = [kubernetes_namespace_v1.logging, helm_release.elasticsearch]
}
