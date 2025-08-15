
# Kafka Deployment in GKE Autopilot with Strimzi, Custom CA, TLS & SCRAM

This document describes how to deploy a **Kafka cluster** in a **GKE Autopilot** cluster using the **Strimzi Kafka Operator**, configured in **KRaft mode** (no ZooKeeper) with:

- **Custom Cluster CA** and **Custom Clients CA** (for TLS trust)
- **TLS-enabled internal listener** (`9093`)
- **SCRAM-SHA-512** authentication for users
- **ClusterIP** services only (Autopilot-compatible)
- Example **KafkaUser** and **KafkaTopic** creation
- Instructions to **retrieve credentials** and **connect clients**

---

## 1. Architecture Overview

**Components:**

- **Namespace:** `kafka` – isolated from system namespaces.
- **Strimzi Kafka Operator** – installed via Helm, scoped to `kafka` namespace.
- **Kafka Cluster:**  
  - 1 broker (KRaft mode)
  - Persistent storage (`standard-rwo`, 20Gi PD-Standard)
  - TLS internal listener (`9093`)
- **Custom Certificates:**  
  - **Cluster CA** – signs broker certificates  
  - **Clients CA** – signs client certificates (for mTLS, if enabled)
- **Entity Operator** – manages KafkaUser and KafkaTopic CRs.
- **KafkaUser:** `dev-user` – SCRAM-SHA-512 authentication.
- **KafkaTopic:** `test-topic`.

---

## 2. Prerequisites

Before running Terraform, ensure you have:

- A **GKE Autopilot cluster** up and running.
- `gcloud`, `kubectl`, `terraform` installed and configured.
- PEM-formatted certificates and keys for **Cluster CA** and **Clients CA**.

Example generation with OpenSSL:

```bash
# Cluster CA
openssl genrsa -out clusterCA.key 4096
openssl req -x509 -new -nodes -key clusterCA.key -sha256 -days 3650 \
  -subj "/CN=dev-kafka-Cluster-CA" -out clusterCA.crt

# Clients CA
openssl genrsa -out clientsCA.key 4096
openssl req -x509 -new -nodes -key clientsCA.key -sha256 -days 3650 \
  -subj "/CN=dev-kafka-Clients-CA" -out clientsCA.crt
```

---

## 3. Terraform Deployment

### File Structure

```
infra/live/dev/kafka/
  versions.tf
  variables.tf
  providers.tf
  ns.tf
  strimzi_helm.tf
  ca_secrets.tf
  kafka_crs.tf
  outputs.tf
  terraform.tfvars
```

### Variables (`terraform.tfvars` example)

```hcl
project_id = "my-gcp-project-id"
region     = "us-central1"
cluster    = "gke-free-autopilot"

cluster_ca_crt_path  = "./certs/clusterCA.crt"
cluster_ca_key_path  = "./certs/clusterCA.key"
clients_ca_crt_path  = "./certs/clientsCA.crt"
clients_ca_key_path  = "./certs/clientsCA.key"
```

### Deploy

```bash
terraform -chdir=infra/live/dev/kafka init
terraform -chdir=infra/live/dev/kafka apply -auto-approve
```

Verify resources:

```bash
kubectl -n kafka get pods
```

---

## 4. Custom CA Integration

Strimzi automatically detects pre-created secrets for CAs:

| Purpose    | Secret Name                 | Keys in Secret     |
| ---------- | --------------------------- | ------------------ |
| Cluster CA | `dev-kafka-cluster-ca`      | `ca.crt`, `ca.key` |
| Cluster CA | `dev-kafka-cluster-ca-cert` | `ca.crt`           |
| Clients CA | `dev-kafka-clients-ca`      | `ca.crt`, `ca.key` |
| Clients CA | `dev-kafka-clients-ca-cert` | `ca.crt`           |

These secrets **must exist before** applying the Kafka CR, otherwise Strimzi will generate its own.

---

## 5. KafkaUser & KafkaTopic

The example Terraform configuration creates:

* **KafkaUser**:

  ```yaml
  apiVersion: kafka.strimzi.io/v1beta2
  kind: KafkaUser
  metadata:
    name: dev-user
    namespace: kafka
    labels:
      strimzi.io/cluster: dev-kafka
  spec:
    authentication:
      type: scram-sha-512
  ```

* **KafkaTopic**:

  ```yaml
  apiVersion: kafka.strimzi.io/v1beta2
  kind: KafkaTopic
  metadata:
    name: test-topic
    namespace: kafka
    labels:
      strimzi.io/cluster: dev-kafka
  spec:
    partitions: 1
    replicas: 1
  ```

---

## 6. Retrieving User Credentials

Get the SCRAM password for `dev-user`:

```bash
kubectl -n kafka get secret dev-user -o jsonpath='{.data.password}' | base64 -d; echo
```

Export Cluster CA for TLS verification:

```bash
kubectl -n kafka get secret dev-kafka-cluster-ca-cert -o jsonpath='{.data.ca\.crt}' | base64 -d > ./clusterCA.crt
```

---

## 7. Connecting to Kafka

### Option A — Local Client via Port-Forward (TLS + SCRAM)

```bash
# 1. Port-forward bootstrap service:
kubectl -n kafka port-forward svc/dev-kafka-kafka-bootstrap 9093:9093

# 2. Get credentials:
PASS=$(kubectl -n kafka get secret dev-user -o jsonpath='{.data.password}' | base64 -d)

# 3. Produce:
kcat -b localhost:9093 -t test-topic -P \
  -X security.protocol=SASL_SSL \
  -X sasl.mechanisms=SCRAM-SHA-512 \
  -X sasl.username=dev-user \
  -X sasl.password="$PASS" \
  -X ssl.ca.location=./clusterCA.crt \
  -X ssl.endpoint.identification.algorithm=

# 4. Consume:
kcat -b localhost:9093 -t test-topic -C -o beginning -q \
  -X security.protocol=SASL_SSL \
  -X sasl.mechanisms=SCRAM-SHA-512 \
  -X sasl.username=dev-user \
  -X sasl.password="$PASS" \
  -X ssl.ca.location=./clusterCA.crt \
  -X ssl.endpoint.identification.algorithm=
```

### Option B — In-Cluster Client with Hostname Verification

```bash
# Run kcat inside the cluster:
kubectl -n kafka run kcat --image=edenhill/kcat:1.7.1 -it --rm --restart=Never -- \
  sh -c '
  PASS=$(kubectl -n kafka get secret dev-user -o jsonpath="{.data.password}" | base64 -d) && \
  kcat -b dev-kafka-kafka-bootstrap.kafka.svc:9093 -L \
    -X security.protocol=SASL_SSL \
    -X sasl.mechanisms=SCRAM-SHA-512 \
    -X sasl.username=dev-user \
    -X sasl.password=$PASS \
    -X ssl.ca.location=/etc/ssl/certs/ca-certificates.crt
  '
```

---

## 8. Notes for Production

* Always enable **TLS** when using SCRAM to avoid sending credentials in cleartext.
* Use **Clients CA** only if mTLS is required; for SASL only, the Cluster CA is sufficient for server-side TLS.
* For external access, configure a **loadbalancer** or **ingress** listener and ensure proper SAN in broker certificates.
* Rotate CA secrets manually and reapply to trigger Strimzi rolling update.

---

## 9. Cleanup

```bash
terraform -chdir=infra/live/dev/kafka destroy -auto-approve
```


