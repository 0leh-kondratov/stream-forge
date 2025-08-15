resource "helm_release" "fluent_bit" {
  name             = "fluent-bit"
  repository       = "https://fluent.github.io/helm-charts"
  chart            = "fluent-bit"
  version          = "0.49.1" # стабильная версия чарта Fluent Bit
  namespace        = kubernetes_namespace_v1.logging.metadata[0].name
  create_namespace = false

  # Требования:
  # - DaemonSet БЕЗ hostNetwork/hostPID/privileged (по умолчанию в чарте).
  # - Разрешённые hostPath только для /var/log и /var/log/containers, readOnly.
  # - Источник логов: /var/log/containers/*.log (CRI), парсер Kubernetes, вывод — Elasticsearch.
  values = [<<-YAML
    service:
      type: ClusterIP

    # Безопасные монтирования для чтения контейнерных логов
    daemonSetVolumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: containers
        hostPath:
          path: /var/log/containers

    daemonSetVolumeMounts:
      - name: varlog
        mountPath: /var/log
        readOnly: true
      - name: containers
        mountPath: /var/log/containers
        readOnly: true

    resources:
      requests:
        cpu: "50m"
        memory: "100Mi"

    # Классическая конфигурация Fluent Bit: Service / Input / Filter / Output
    # Чтение CRI-логов, Kubernetes‑enrichment, отправка в Elasticsearch.
    config:
      service: |
        [SERVICE]
            Flush        1
            Daemon       Off
            Parsers_File parsers.conf
            HTTP_Server  Off

      inputs: |
        [INPUT]
            Name              tail
            Path              /var/log/containers/*.log
            Tag               kube.var.log.containers.*
            Parser            cri
            Mem_Buf_Limit     5MB
            Skip_Long_Lines   On
            Refresh_Interval  10

      filters: |
        [FILTER]
            Name                kubernetes
            Match               kube.var.log.containers.*
            Kube_URL            https://kubernetes.default.svc:443
            Merge_Log           On
            Keep_Log            Off
            Kube_Tag_Prefix     kube.var.log.containers.

      outputs: |
        [OUTPUT]
            Name            es
            Match           *
            Host            elasticsearch-master.logging.svc
            Port            9200
            Logstash_Format On
            Replace_Dots    On
            Retry_Limit     False

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
