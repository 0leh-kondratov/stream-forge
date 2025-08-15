# ===== Удобные команды для проверки и отладки (TLS + SCRAM) =====

# Проброс TLS bootstrap-сервиса на localhost:9093
output "port_forward_bootstrap_tls" {
  description = "Проброс TLS bootstrap на localhost:9093 (внутренний TLS-listener)"
  value = <<-EOT
    kubectl -n kafka port-forward svc/dev-kafka-kafka-bootstrap 9093:9093
  EOT
}

# Получить пароль пользователя dev-user (SCRAM-SHA-512)
output "get_dev_user_password" {
  description = "Получить пароль SCRAM для KafkaUser dev-user"
  value = <<-EOT
    kubectl -n kafka get secret dev-user -o jsonpath='{.data.password}' | base64 -d; echo
  EOT
}

# Выгрузить Cluster CA в локальный файл для TLS trust
output "save_cluster_ca_locally" {
  description = "Выгрузить Cluster CA в локальный файл ./clusterCA.crt"
  value = <<-EOT
    kubectl -n kafka get secret dev-kafka-cluster-ca-cert -o jsonpath='{.data.ca\\.crt}' | base64 -d > ./clusterCA.crt
  EOT
}

# Локальные примеры kcat через port-forward (TLS+SCRAM), без проверки hostname
output "kcat_local_tls_scram_examples" {
  description = "Примеры kcat локально через port-forward (TLS+SCRAM, без hostname verification)"
  value = <<-EOT
    # 1) В одном терминале:
    kubectl -n kafka port-forward svc/dev-kafka-kafka-bootstrap 9093:9093

    # 2) В другом терминале: выгрузить Cluster CA и пароль:
    kubectl -n kafka get secret dev-kafka-cluster-ca-cert -o jsonpath='{.data.ca\\.crt}' | base64 -d > ./clusterCA.crt
    PASS=$(kubectl -n kafka get secret dev-user -o jsonpath='{.data.password}' | base64 -d)

    # 3) Producer (вводите строки, завершите Ctrl-D):
    kcat -b localhost:9093 -t test-topic -P \
      -X security.protocol=SASL_SSL \
      -X sasl.mechanisms=SCRAM-SHA-512 \
      -X sasl.username=dev-user \
      -X sasl.password="$PASS" \
      -X ssl.ca.location=./clusterCA.crt \
      -X ssl.endpoint.identification.algorithm=

    # 4) Consumer:
    kcat -b localhost:9093 -t test-topic -C -o beginning -q \
      -X security.protocol=SASL_SSL \
      -X sasl.mechanisms=SCRAM-SHA-512 \
      -X sasl.username=dev-user \
      -X sasl.password="$PASS" \
      -X ssl.ca.location=./clusterCA.crt \
      -X ssl.endpoint.identification.algorithm=
  EOT
}

# Пример изнутри кластера c проверкой hostname (рекомендуется для prod)
output "kcat_in_pod_tls_scram" {
  description = "Запустить kcat внутри кластера c TLS+SCRAM и проверкой hostname (использует bootstrap DNS)"
  value = <<-EOT
    # Сохранить Cluster CA в ConfigMap (однократно)
    kubectl -n kafka create configmap cluster-ca --from-literal=ca.crt="$(kubectl -n kafka get secret dev-kafka-cluster-ca-cert -o jsonpath='{.data.ca\\.crt}' | base64 -d)" --dry-run=client -o yaml | kubectl apply -f -

    # Создать pod, где kcat видит CA-файл как /etc/ssl/private/clusterCA.crt
    kubectl -n kafka run kcat --image=edenhill/kcat:1.7.1 --restart=Never -it --rm \
      --overrides='
      {
        "apiVersion":"v1","kind":"Pod",
        "metadata":{"name":"kcat"},
        "spec":{
          "containers":[
            {
              "name":"kcat",
              "image":"edenhill/kcat:1.7.1",
              "stdin":true,"tty":true,
              "volumeMounts":[{"name":"ca","mountPath":"/etc/ssl/private"}]
            }
          ],
          "volumes":[{"name":"ca","configMap":{"name":"cluster-ca","items":[{"key":"ca.crt","path":"clusterCA.crt"}]}}]
        }
      }' -- sh -lc "
        PASS=$(kubectl -n kafka get secret dev-user -o jsonpath='{.data.password}' | base64 -d) && \
        kcat -b dev-kafka-kafka-bootstrap.kafka.svc:9093 -L \
          -X security.protocol=SASL_SSL \
          -X sasl.mechanisms=SCRAM-SHA-512 \
          -X sasl.username=dev-user \
          -X sasl.password=\$PASS \
          -X ssl.ca.location=/etc/ssl/private/clusterCA.crt
      "
  EOT
}
