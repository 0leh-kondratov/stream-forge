## Part V: Technical Details and Appendices

This section of the document contains detailed technical specifications and additional materials intended for an in-depth study of the StreamForge platform's architecture and implementation.

### Appendix A: Data Schemas and API

This section presents the full technical specifications of the API for `queue-manager`, including detailed JSON schemas for all types of messages circulating in Apache Kafka. This data is intended for developers and system architects interested in a deep understanding of the internal structure and interaction of system components.

### Appendix B: Kubernetes Manifest Examples

This appendix provides examples of Kubernetes manifests illustrating the deployment and configuration of various StreamForge components in the cluster.

#### Example: Kubernetes Job for `arango-candles`

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: job-arango-candles-btcusdt-abc123
  namespace: stf
  labels:
    app: streamforge
    queue_id: "wf-btcusdt-api_candles_1m-20240801-abc123"
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: arango-candles
          image: registry.dmz.home/streamforge/arango-candles:v0.1.5
          env:
            - name: QUEUE_ID
              value: "wf-btcusdt-api_candles_1m-20240801-abc123"
            - name: SYMBOL
              value: "BTCUSDT"
            - name: TYPE
              value: "api_candles_1m"
            - name: KAFKA_TOPIC
              value: "wf-btcusdt-api_candles_1m-20240801-abc123-data"
            - name: COLLECTION_NAME
              value: "btcusdt_api_candles_1m_2024_08_01"
            # ... other variables from ConfigMap and Secret ...
      nodeSelector:
        streamforge-worker: "true" # Example selector for dedicated nodes
  backoffLimit: 2
  ttlSecondsAfterFinished: 3600
```

### Appendix C: CI/CD Pipeline Examples

This section presents complete `.gitlab-ci.yml` files for each microservice, demonstrating the implemented testing, building, and deployment (CI/CD) processes within the StreamForge platform.

### Appendix D: Glossary of Terms

This glossary provides definitions of key terms and concepts used in the StreamForge documentation, including notions such as Workflow, Job, Decoupling, Idempotence, and others, to ensure consistency of understanding and technical accuracy.

### Appendix E: Deployment and Operations Guide

This guide contains step-by-step instructions for deploying the StreamForge platform from scratch, as well as recommendations for its monitoring, backup procedures, and updates, ensuring full lifecycle management of the system.

### Appendix F: Testing Procedure

To verify the functionality of the StreamForge system, specialized tools `dummy-service` and `debug_producer.py` are used. These tools demonstrate particular effectiveness in the standardized `devcontainer` development environment.

**1. `dummy-service`: Test Microservice for Simulation**

`dummy-service` is designed to simulate the behavior of various services, verify connectivity with Apache Kafka, and simulate various load scenarios.

*   **Launch:** The service can be launched in Kubernetes as a `Job` or `Pod`. For local testing in `devcontainer`, the following command is used:
    ```bash
    python3.11 -m app.main --debug --simulate-loading
    ```
*   **Further Information:** A detailed description is available in `services/dummy-service/README.md`.

**2. `debug_producer.py`: Command-Line Tool for Sending Commands and Verifying Responses**

This CLI tool is used to send test commands (`ping`, `stop`) to Apache Kafka and subsequently verify the received responses.

*   **Kafka Connectivity Testing (ping/pong):**
    ```bash
    python3.11 services/dummy-service/debug_producer.py \
      --queue-id <your-queue-id> \
      --command ping \
      --expect-pong
    ```
*   **Stop Command Testing (stop):**
    ```bash
    python3.11 services/dummy-service/debug_producer.py \
      --queue-id <your-queue-id> \
      --command stop
    ```
*   **Load Simulation and Status Tracking Testing:** Launching `dummy-service` with the `--simulate-loading` flag allows monitoring events in the `queue-events` topic.

*   **Failure Simulation Testing:** Launching `dummy-service` with the `--fail-after N` parameter allows observing the sending of `error` events.
*   **Prometheus Metrics Testing:** Metrics are checked using `curl localhost:8000/metrics`.

**3. `devcontainer`: Standardized Development Environment**

`devcontainer` is a Docker container that provides a full-fledged development environment integrated with VS Code. This ensures a unified environment for all project developers.

**Key Features:**
*   **Base Image:** Ubuntu 22.04 LTS.
*   **Tools:** Includes pre-installed tools such as `kubectl`, Helm, `gitlab-runner`, `git`, `curl`, `ssh`, and others.
*   **Kubernetes Access:** Automatic configuration of access to the Kubernetes cluster.
*   **Users and SSH:** Creation of a separate user and configuration of SSH access.
*   **Certificates:** Installation of CA certificates to ensure trust in internal services.

**Usage Instructions:**
1.  Install Docker Desktop and the "Dev Containers" extension for VS Code.
2.  Open the StreamForge project in VS Code and select "Reopen in Container."
3.  VS Code will automatically build the image and launch the container.

### Appendix G: Kafka Resource Management

Kubernetes manifests located in the `cred-kafka-yaml/` directory provide declarative management of Apache Kafka resources through the Strimzi operator. This includes the creation of topics (`queue-control`, `queue-events`), management of Kafka users (`user-streamforge`) and their access rights, as well as secure storage of credentials.

### Appendix H: Kubernetes Debugging Environment

For debugging and interacting with the Kubernetes cluster, StreamForge uses the following tools and approaches:

*   **JupyterHub:** Provides the ability to launch interactive Jupyter Notebook sessions directly within the Kubernetes cluster. The Jupyter Notebook images used in the platform already contain necessary tools such as `kubectl`, `helm`, and others.

    **Key Features of JupyterHub Setup:**
    *   **Idle Server Management:** Automatic termination of idle Jupyter servers to optimize resource utilization.
    *   **Authentication:** Simple "dummy" authentication is used for the test environment.
    *   **Base Database:** `sqlite-memory` is used, but data is persisted on the host.
    *   **Pod Placement:** Hub and user servers are launched on node `k2w-8`.
    *   **Access:** Via Ingress at `jupyterhub.dmz.home` with TLS.
    *   **User Server Images:** A custom image `registry.dmz.home/streamforge/core-modules/jupyter-python311:v0.0.2` with necessary tools is used.
    *   **Resources:** Guaranteed memory allocation for each server — `1G`.
    *   **Data Storage:** Persistent volumes mounted from the host are used for `/home/`, `/data/project`, `/data/venv`.
    *   **Security:** Pods are launched with `UID: 1001` and `FSGID: 100`.
    *   **Docker Registry:** The `regcred` secret is used for authentication.

*   **Dev Container (VS Code):** Described in detail in Appendix F.

*   **Dev-container (general):** This is a universal Docker image containing a wide range of tools (`kubectl`, `helm`, `kafkacat`, `python`) that can be used to launch temporary pods in Kubernetes for interactive debugging and administration.

```