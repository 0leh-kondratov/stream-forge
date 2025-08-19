# Kafka Deployment with Strimzi on GKE

This directory contains Terraform code to deploy a Kafka cluster on Google Kubernetes Engine (GKE) using the Strimzi Kafka operator.

## Prerequisites

*   [Terraform](https://www.terraform.io/downloads.html) installed (version >= 1.6.0).
*   [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) installed.
*   [Helm](https://helm.sh/docs/intro/install/) installed.
*   [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated.
*   A GKE cluster already provisioned and configured in your `kubeconfig`.
*   Your `gcloud` application default credentials configured (`gcloud auth application-default login`).

## Deployment

1.  **Navigate to the deployment directory:**
    ```bash
    cd /data/projects/stream-forge/infra/live/dev/kafka
    ```

2.  **Initialize Terraform:**
    This step downloads the necessary providers and modules.
    ```bash
    terraform init
    ```

3.  **Review the plan (Optional but Recommended):**
    This command shows you what Terraform will do before making any changes.
    ```bash
    terraform plan
    ```

4.  **Apply the changes:**
    This command applies the Terraform configuration to deploy the Kafka cluster.
    ```bash
    terraform apply
    ```
    Type `yes` when prompted to confirm the deployment.

## Staged Installation (Optional)

If you want to deploy the components in stages, you can use the `-target` option with `terraform apply`. This can be useful for debugging or for a more controlled rollout.

### Stage 1: Install Strimzi Operator

This will install the Strimzi operator and wait for the Custom Resource Definitions (CRDs) to be ready.

```bash
terraform apply -target=module.strimzi_operator -target=time_sleep.pause_after_operator -target=null_resource.wait_crds -auto-approve
```

### Stage 2: Install Kafka Cluster

This will create the Kafka cluster custom resource and wait for the cluster to be ready.

```bash
terraform apply -target=module.kafka_cluster -target=time_sleep.pause_after_cluster -target=null_resource.wait_kafka_ready -auto-approve
```

### Stage 3: Install Kafka Objects (Topics/Users)

This will create the Kafka topics and users.

```bash
terraform apply -target=module.kafka_objects -auto-approve
```

## Checking Deployment Status

After running `terraform apply`, you can check the status of your Kafka cluster:

1.  **Check Strimzi Operator status:**
    ```bash
    kubectl get deployment strimzi-cluster-operator -n kafka
    kubectl get pods -l name=strimzi-cluster-operator -n kafka
    ```

2.  **Check Kafka Custom Resource status:**
    ```bash
    kubectl get kafka k3 -n kafka -o yaml
    ```
    Look for `status.conditions` and ensure `type: Ready` is `True`.

3.  **Check Kafka Broker Pods:**
    ```bash
    kubectl get pods -l strimzi.io/cluster=k3 -n kafka
    ```
    All pods (e.g., `k3-kafka-0`, `k3-kafka-1`, `k3-kafka-2`) should eventually be `Running` and `Ready`.

4.  **Check KafkaNodePool status:**
    ```bash
    kubectl get kafkanodepool combined -n kafka -o yaml
    ```

## Accessing Kafka Credentials

This deployment creates a Kafka user named `user-streamforge`. Strimzi automatically creates a Kubernetes Secret containing the credentials for this user.

1.  **Get the Secret name:**
    ```bash
    kubectl get secret -n kafka | grep user-streamforge
    ```
    The secret name will typically be `user-streamforge`.

2.  **Decode the credentials:**
    The username and password are Base64 encoded within the secret.
    ```bash
    kubectl get secret user-streamforge -n kafka -o jsonpath='{.data.password}' | base64 -d
    kubectl get secret user-streamforge -n kafka -o jsonpath='{.data.username}' | base64 -d
    ```

3.  **Get Kafka Broker Addresses:**
    ```bash
    kubectl get service k3-kafka-brokers -n kafka -o jsonpath='{.spec.clusterIP}:9092'
    ```
    For external access, you might need to configure an external listener in `kafka.yaml` and expose it via a Kubernetes Service (e.g., LoadBalancer or NodePort).

## Creating Kafka Objects (Topics and Users)

This deployment automatically creates `queue-control` and `queue-events` topics, and `user-streamforge` user. If you need to create additional topics or users, you can define them as `KafkaTopic` or `KafkaUser` custom resources.

Example `KafkaTopic` (save as `my-new-topic.yaml`):
```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: my-new-topic
  namespace: kafka
  labels:
    strimzi.io/cluster: k3 # Must match your Kafka cluster name
spec:
  partitions: 3
  replicas: 3
  config:
    retention.ms: "604800000" # 7 days
```
Apply with: `kubectl apply -f my-new-topic.yaml -n kafka`

Example `KafkaUser` (save as `my-new-user.yaml`):
```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaUser
metadata:
  name: my-new-user
  namespace: kafka
  labels:
    strimzi.io/cluster: k3 # Must match your Kafka cluster name
spec:
  authentication:
    type: scram-sha-512
  authorization:
    type: simple
    acls:
      - resource:
          type: topic
          name: my-new-topic
          patternType: literal
        operation: All
        host: "*"
```
Apply with: `kubectl apply -f my-new-user.yaml -n kafka`

## Testing Kafka Connectivity

You can use a Kafka client (e.g., `kcat` or `kafkacat`) to test connectivity.

1.  **Install `kcat` (if not already installed):**
    ```bash
    sudo apt-get update && sudo apt-get install kcat # For Debian/Ubuntu
    # brew install kcat # For macOS
    ```

2.  **Get Kafka Broker Address:**
    ```bash
    BROKER=$(kubectl get service k3-kafka-brokers -n kafka -o jsonpath='{.spec.clusterIP}:9092')
    ```

3.  **Get User Credentials:**
    ```bash
    USERNAME=$(kubectl get secret user-streamforge -n kafka -o jsonpath='{.data.username}' | base64 -d)
    PASSWORD=$(kubectl get secret user-streamforge -n kafka -o jsonpath='{.data.password}' | base64 -d)
    ```

4.  **Produce a message (example for `queue-control` topic):**
    ```bash
    echo "Hello from Terraform!" | kcat -b $BROKER -t queue-control -X security.protocol=SASL_PLAINTEXT -X sasl.mechanisms=SCRAM-SHA-512 -X sasl.username=$USERNAME -X sasl.password=$PASSWORD -P
    ```

5.  **Consume messages (example for `queue-control` topic):**
    ```bash
    kcat -b $BROKER -t queue-control -X security.protocol=SASL_PLAINTEXT -X sasl.mechanisms=SCRAM-SHA-512 -X sasl.username=$USERNAME -X sasl.password=$PASSWORD -C -o beginning
    ```

## Troubleshooting

*   **Check Strimzi Operator Logs:** `kubectl logs -f deployment/strimzi-cluster-operator -n kafka`
*   **Check Kafka Pod Logs:** `kubectl logs -f <kafka-pod-name> -n kafka`
*   **Terraform State Issues:** If Terraform state gets out of sync, consider `terraform plan -refresh-only` or `terraform state rm` (use with caution).
