# ЭТАП 1: оператор Strimzi
module "strimzi_operator" {
  source    = "./modules/strimzi-operator"
  namespace = var.namespace
}

# Небольшая пауза после установки чарта, чтобы webhook/CRD стабилизировались
resource "time_sleep" "pause_after_operator" {
  depends_on      = [module.strimzi_operator]
  create_duration = "${var.pause_after_operator_sec}s"
}

# Явное ожидание регистрации CRD (Established)
resource "null_resource" "wait_crds" {
  depends_on = [time_sleep.pause_after_operator]

  provisioner "local-exec" {
    command = <<-EOT
      set -euo pipefail
      kubectl wait --for=condition=Established crd/kafkas.kafka.strimzi.io --timeout=180s
      kubectl wait --for=condition=Established crd/kafkatopics.kafka.strimzi.io --timeout=180s
      kubectl wait --for=condition=Established crd/kafkausers.kafka.strimzi.io --timeout=180s
    EOT
    interpreter = ["/bin/bash", "-lc"]
  }
}

# ЭТАП 2: кластер Kafka (CR Kafka)
module "kafka_cluster" {
  source     = "./modules/kafka-cluster"
  namespace  = var.namespace
  kafka_name = var.kafka_name
  replicas   = var.kafka_replicas

  # Важно: кластер создаём только после CRD
  depends_on = [null_resource.wait_crds]
}

# Пауза/стабилизация стейтфулсетов после CR Kafka
resource "time_sleep" "pause_after_cluster" {
  depends_on      = [module.kafka_cluster]
  create_duration = "${var.pause_after_cluster_sec}s"
}

# Ждём, пока CR Kafka перейдёт в Ready
resource "null_resource" "wait_kafka_ready" {
  depends_on = [time_sleep.pause_after_cluster]

  triggers = {
    kafka_name = var.kafka_name
    namespace  = var.namespace
  }

  provisioner "local-exec" {
    command     = "kubectl wait kafka/${self.triggers.kafka_name} -n ${self.triggers.namespace} --for=condition=Ready --timeout=20m"
    interpreter = ["/bin/bash", "-lc"]
  }
}

# ЭТАП 3: объекты Kafka (topics/users)
module "kafka_objects" {
  source     = "./modules/kafka-objects"
  namespace  = var.namespace
  kafka_name = var.kafka_name

  # Создаём только после полной готовности кластера
  depends_on = [null_resource.wait_kafka_ready]
}
