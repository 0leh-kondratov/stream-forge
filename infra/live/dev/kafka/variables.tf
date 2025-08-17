variable "project_id" { type = string }
variable "region"     { type = string  default = "us-central1" }

variable "namespace"  { type = string  default = "kafka" }

# Паузы между этапами (секунды)
variable "pause_after_operator_sec" { type = number default = 20 }
variable "pause_after_cluster_sec"  { type = number default = 10 }

# Параметры кластера Kafka
variable "kafka_name"     { type = string  default = "k3" }
variable "kafka_replicas" { type = number  default = 3 }
variable "kafka_version"  { type = string  default = "3.6.0" }
