# Kafka (KRaft, без ZooKeeper), 1 брокер, внутренний TLS-listener, PD-Standard 20Gi
resource "kubernetes_manifest" "kafka_cluster" {
  manifest = {
    apiVersion = "kafka.strimzi.io/v1beta2"
    kind       = "Kafka"
    metadata = {
      name      = "dev-kafka"
      namespace = kubernetes_namespace_v1.kafka.metadata[0].name
    }
    spec = {
      kafka = {
        version  = "3.7.0"
        replicas = 1

        # Внутренний TLS listener (рекомендуется вместе со SCRAM)
        listeners = [
          {
            name = "internal"
            port = 9093
            type = "internal"
            tls  = true
            # Если хотите свой кастомный cert для listener без замены CA — можно добавить:
            # configuration = {
            #   brokerCertChainAndKey = {
            #     secretName  = "kafka-listener-tls"
            #     certificate = "tls.crt"
            #     key         = "tls.key"
            #   }
            # }
          }
        ]

        # Хранилище — PersistentVolumeClaim (PD-Standard)
        storage = {
          type  = "persistent-claim"
          size  = "20Gi"
          class = "standard-rwo"
        }

        # Запросы ресурсов на брокер (Autopilot сам подберёт лимиты)
        resources = {
          requests = {
            cpu    = "1"
            memory = "2Gi"
          }
        }

        # Конфигурация под однонодовый кластер (KRaft)
        config = {
          "auto.create.topics.enable"                = "false"
          "offsets.topic.replication.factor"         = 1
          "transaction.state.log.replication.factor" = 1
          "transaction.state.log.min.isr"            = 1
        }

        # (опционально) Запускать на Spot-нодах:
        # template = {
        #   pod = {
        #     spec = {
        #       nodeSelector = {
        #         "cloud.google.com/gke-spot" = "true"
        #       }
        #     }
        #   }
        # }
      }

      # Включаем Entity Operator (Topic + User) с небольшими requests
      entityOperator = {
        topicOperator = {
          resources = {
            requests = {
              cpu    = "100m"
              memory = "256Mi"
            }
          }
        }
        userOperator = {
          resources = {
            requests = {
              cpu    = "100m"
              memory = "256Mi"
            }
          }
        }
      }
    }
  }

  # Дожидаемся установки оператора и наличия наших кастомных CA-секретов
  depends_on = [
    helm_release.strimzi,
    kubernetes_secret_v1.dev_kafka_cluster_ca,
    kubernetes_secret_v1.dev_kafka_cluster_ca_cert,
    kubernetes_secret_v1.dev_kafka_clients_ca,
    kubernetes_secret_v1.dev_kafka_clients_ca_cert
  ]
}

# Пользователь SCRAM-SHA-512 (секрет с паролем создаст Strimzi)
resource "kubernetes_manifest" "kafka_user" {
  manifest = {
    apiVersion = "kafka.strimzi.io/v1beta2"
    kind       = "KafkaUser"
    metadata = {
      name      = "dev-user"
      namespace = kubernetes_namespace_v1.kafka.metadata[0].name
      labels = {
        "strimzi.io/cluster" = "dev-kafka"
      }
    }
    spec = {
      authentication = {
        type = "scram-sha-512"
      }
      # При необходимости добавляйте authorizations (ACL) здесь
    }
  }

  depends_on = [kubernetes_manifest.kafka_cluster]
}

# Тестовый топик
resource "kubernetes_manifest" "kafka_topic" {
  manifest = {
    apiVersion = "kafka.strimzi.io/v1beta2"
    kind       = "KafkaTopic"
    metadata = {
      name      = "test-topic"
      namespace = kubernetes_namespace_v1.kafka.metadata[0].name
      labels = {
        "strimzi.io/cluster" = "dev-kafka"
      }
    }
    spec = {
      partitions = 1
      replicas   = 1
    }
  }

  depends_on = [kubernetes_manifest.kafka_cluster]
}
