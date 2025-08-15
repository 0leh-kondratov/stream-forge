resource "kubernetes_namespace_v1" "observability" {
  metadata { name = "observability" }
}

resource "helm_release" "kps" {
  name       = "kps"
  namespace  = kubernetes_namespace_v1.observability.metadata[0].name
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  # version  = "76.3.0"

  # более надёжная установка
  wait            = true
  timeout         = 600
  atomic          = true
  cleanup_on_fail = true

  values = [<<-YAML
    grafana:
      adminUser: admin
      adminPassword: ${var.grafana_admin_password}
      service:
        type: ClusterIP
      ingress:
        enabled: false

    alertmanager:
      service:
        type: ClusterIP
      alertmanagerSpec:
        resources:
          requests:
            cpu: 50m
            memory: 128Mi

    prometheus:
      service:
        type: ClusterIP
      prometheusSpec:
        retention: 15d
        storageSpec:
          emptyDir: {}      
        resources:
          requests:
            cpu: 200m
            memory: 512Mi
  
    prometheus-node-exporter:
      enabled: false
    nodeExporter:
      enabled: false

    kubeApiServer:
      enabled: false
    kubeDns:
      enabled: false
    kubeProxy:
      enabled: false
    kubeControllerManager:
      enabled: false
    kubeScheduler:
      enabled: false
    kubeEtcd:
      enabled: false

    # не создавать kubelet service в kube-system
    prometheusOperator:
      kubeletService:
        enabled: false

    kubelet:
      serviceMonitor:
        enabled: false
      # enabled: false  

    kube-state-metrics:
      resources:
        requests:
          cpu: 50m
          memory: 100Mi
  YAML
  ]

  depends_on = [kubernetes_namespace_v1.observability]
}
