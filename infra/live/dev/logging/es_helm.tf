resource "helm_release" "elasticsearch" {
  name             = "elasticsearch"
  repository       = "https://helm.elastic.co"
  chart            = "elasticsearch"
  version          = "8.5.1" # зафиксированная стабильная версия
  namespace        = kubernetes_namespace_v1.logging.metadata[0].name
  create_namespace = false

  # Autopilot: экономные requests/limits; PVC на PD-Standard (HDD) 20Gi.
  # Dev-only: выключаем security и переводим на HTTP, чтобы работал curl и коннект Kibana.
  values = [<<-YAML
    replicas: 1
    minimumMasterNodes: 1

    protocol: http

    esConfig:
      elasticsearch.yml: |
        xpack.security.enabled: false
        discovery.type: single-node

    resources:
      requests:
        cpu: "500m"
        memory: "2Gi"
      limits:
        cpu: "1"
        memory: "2Gi"

    volumeClaimTemplate:
      accessModes: ["ReadWriteOnce"]
      storageClassName: "standard"   # GKE StorageClass, соответствующий pd-standard (HDD) в ряде конфигураций
      resources:
        requests:
          storage: 20Gi

    service:
      type: ClusterIP

    # Это минимальная dev-конфигурация. Не используйте в проде.
    # Пример для Spot (закомментировано):
    # nodeSelector:
    #   cloud.google.com/gke-spot: "true"
  YAML
  ]

  wait             = true
  timeout          = 600
  atomic           = true
  cleanup_on_fail  = true

  depends_on = [kubernetes_namespace_v1.logging]
}
