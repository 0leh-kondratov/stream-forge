# Namespace
resource "kubernetes_namespace" "observability" {
  metadata { name = var.observability_namespace }
}

# (Рекомендовано) kube-state-metrics — лёгкий и Autopilot-friendly
resource "helm_release" "kube_state_metrics" {
  count      = var.install_kube_state_metrics ? 1 : 0
  name       = "kube-state-metrics"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-state-metrics"
  namespace  = kubernetes_namespace.observability.metadata[0].name

  set = [
    {
      name  = "resources.requests.cpu"
      value = "50m"
    },
    {
      name  = "resources.requests.memory"
      value = "64Mi"
    },
    {
      name  = "resources.limits.cpu"
      value = "200m"
    },
    {
      name  = "resources.limits.memory"
      value = "256Mi"
    }
  ]

  depends_on = [kubernetes_namespace.observability]
}

# Alloy — ручной конфиг с ЯВНЫМИ правилами (метрики+логи). Без hostPath, совместимо с Autopilot.
resource "helm_release" "alloy_manual" {
  name       = "alloy-manual"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "alloy"
  namespace  = kubernetes_namespace.observability.metadata[0].name

  # Controller: deployment (достаточно для pod-логов и scrapes через API)
  set = [
    {
      name  = "controller.type"
      value = "deployment"
    },
    {
      name  = "alloy.resources.requests.cpu"
      value = "100m"
    },
    {
      name  = "alloy.resources.requests.memory"
      value = "256Mi"
    },
    {
      name  = "alloy.resources.limits.cpu"
      value = "500m"
    },
    {
      name  = "alloy.resources.limits.memory"
      value = "512Mi"
    },
    {
      name  = "alloy.podSecurityContext.runAsNonRoot"
      value = "true"
    },
    {
      name  = "alloy.containerSecurityContext.allowPrivilegeEscalation"
      value = "false"
    },
    {
      name  = "alloy.containerSecurityContext.readOnlyRootFilesystem"
      value = "true"
    }
  ]

  # Полный рабочий config.alloy (метрики + логи; трассы закомментированы)
  values = [<<-YAML
    alloy:
      config: |
        logging {
          level  = "debug"
          format = "logfmt"
        }

        // ===== Kubernetes discovery =====
        discovery.kubernetes "pods"        { role = "pod" }
        discovery.kubernetes "nodes"       { role = "node" }
        discovery.kubernetes "services"    { role = "service" }
        discovery.kubernetes "endpoints"   { role = "endpoints" }
        discovery.kubernetes "endpointslices" { role = "endpointslice" }
        discovery.kubernetes "ingresses"   { role = "ingress" }

        // ===== Prometheus scrapes =====
        // kube-state-metrics (если выше включён release kube-state-metrics)
        prometheus.scrape "kube_state_metrics" {
          targets         = discovery.kubernetes.services.targets
          job_name        = "kube-state-metrics"
          scrape_interval = "30s"
          relabel_rules = <<EOF
          rule { source_labels = ["__meta_kubernetes_service_label_app_kubernetes_io_name"]; regex = "kube-state-metrics"; action = "keep" }
          EOF
          forward_to = [prometheus.remote_write.grafana_cloud.receiver]
        }

        // Все поды кластера (собираем то, что экспонирует /metrics)
        prometheus.scrape "kubernetes_pods" {
          targets         = discovery.kubernetes.pods.targets
          job_name        = "kubernetes-pods"
          scrape_interval = "30s"
          // пример исключений (необязательно)
          relabel_rules = <<EOF
          rule { source_labels = ["__meta_kubernetes_pod_label_app_kubernetes_io_name"]; regex = "alloy.*"; action = "drop" }
          EOF
          forward_to = [prometheus.remote_write.grafana_cloud.receiver]
        }

        // Push в Grafana Cloud Prometheus (remote_write /push)
        prometheus.remote_write "grafana_cloud" {
          endpoint {
            url = "${trim(var.grafana_cloud_prometheus_remote_write_endpoint, "/")}/push"
            basic_auth {
              username = "${var.grafana_cloud_prometheus_user}"
              password = "${var.grafana_cloud_prometheus_api_key}"
            }
          }
          external_labels = { cluster = "${var.cluster_name}" }
        }

        // ===== Pod logs через Kubernetes API → Loki =====
        loki.source.kubernetes "pods" {
          targets    = discovery.kubernetes.pods.targets
          forward_to = [loki.process.pods.receiver]
        }

        loki.process "pods" {
          forward_to = [loki.write.gc.receiver]
          stage.label {
            values = {
              "processed_by" = "alloy"
            }
          }
        }

        // События кластера → Loki (полезно для отладки)
        loki.source.kubernetes_events "events" {
          forward_to = [loki.write.gc.receiver]
        }

        loki.write "gc" {
          endpoint {
            url = "${trim(var.grafana_cloud_loki_endpoint, "/")}/loki/api/v1/push"
            basic_auth {
              username = "${var.grafana_cloud_loki_user}"
              password = "${var.grafana_cloud_loki_api_key}"
            }
          }
          external_labels = { cluster = "${var.cluster_name}" }
        }

        // ===== (Optional) OTLP traces → Tempo =====
        // Раскомментируйте, если заданы endpoint/token
        %{ if var.grafana_tempo_otlp_endpoint != "" }
        otelcol.receiver.otlp "in" {
          protocols { http {} grpc {} }
          output { traces = [otelcol.exporter.otlp.tempo.input] }
        }

        otelcol.exporter.otlp "tempo" {
          client {
            endpoint = "${var.grafana_tempo_otlp_endpoint}"
            headers  = { "Authorization" = "Bearer ${var.grafana_tempo_token}" }
          }
        }
        %{ endif }
    YAML
  ]

  timeout  = 600
  wait     = true

  depends_on = [
    kubernetes_namespace.observability
    # порядок с kube_state_metrics не критичен — discovery динамический
  ]
}