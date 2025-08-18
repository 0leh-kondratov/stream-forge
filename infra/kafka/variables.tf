variable "kubeconfig" {
  description = "Path to kubeconfig"
  type        = string
  default     = "~/.kube/config"
}

variable "namespace" {
  description = "Namespace for Strimzi and Kafka"
  type        = string
  default     = "kafka"
}

variable "ingress_class" {
  description = "IngressClass for external listener"
  type        = string
  default     = "traefik"
}

variable "domain" {
  description = "Base domain (e.g. dmz.home)"
  type        = string
  default     = "dmz.home"
}

variable "cluster_name" {
  description = "Kafka cluster name"
  type        = string
  default     = "k3"
}

variable "storage_class" {
  description = "StorageClass for Kafka and ZK PVCs"
  type        = string
  default     = "linstor-storage"
}

variable "kafka_replicas" {
  description = "Number of Kafka brokers"
  type        = number
  default     = 3
}

variable "zk_replicas" {
  description = "Number of Zookeeper nodes"
  type        = number
  default     = 3
}

variable "bootstrap_host" {
  description = "External bootstrap DNS name"
  type        = string
  default     = "k3-kafka-bootstrap.kafka.dmz.home"
}

variable "broker_hosts" {
  description = "Per-broker external DNS names (index = broker id)"
  type        = list(string)
  default     = [
    "k3-kafka-0.kafka.dmz.home",
    "k3-kafka-1.kafka.dmz.home",
    "k3-kafka-2.kafka.dmz.home",
  ]
}

variable "topics" {
  description = "List of topic specs"
  type = list(object({
    name           = string
    partitions     = number
    replicas       = number
    retention_ms   = number
    cleanup_policy = string
  }))
  default = [
    { name = "queue-control", partitions = 3, replicas = 3, retention_ms = 86400000,  cleanup_policy = "delete" },
    { name = "queue-events",  partitions = 3, replicas = 3, retention_ms = 604800000, cleanup_policy = "delete" },
  ]
}

variable "create_user_streamforge" {
  description = "Create KafkaUser user-streamforge"
  type        = bool
  default     = true
}
