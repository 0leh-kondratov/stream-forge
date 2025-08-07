## Part III: Infrastructure and Environment

The **StreamForge** platform is deployed within a high-performance local laboratory and is built upon a foundation of open technologies, focused on ensuring reliability, scalability, and manageability. The central element of the infrastructure is a **Kubernetes** cluster, operating in a virtualized environment and utilizing modern DevOps methodologies and cloud architectural patterns.

### Chapter 5: Platform Fundamentals: Kubernetes and Virtualization

#### 5.1. Foundation: Proxmox VE

**Proxmox VE** is used as the base virtualization layer—a mature, enterprise-grade platform that provides isolation of computing environments, high availability, and centralized resource management. Virtual machines deployed on Proxmox VE, serve as hosts for Kubernetes cluster nodes.

#### 5.2. Cluster Deployment: Kubespray

The Kubernetes cluster is deployed using **Kubespray**—an automated tool recommended by CNCF for production environments. Kubespray ensures an idempotent and repeatable setup process, including the installation of control-plane components, configuration of network topology, and integration with TLS solutions, guaranteeing consistency and reproducibility of deployment.

#### 5.3. Network Infrastructure

StreamForge's network infrastructure is designed to ensure high reliability and adaptability, focusing on fault tolerance and transparent external access:

- **kube-vip** provides a virtual IP address for High Availability (HA) access to the Kubernetes API, allowing automatic traffic redirection in case of a control plane node failure.
- **MetalLB** version `0.14.9` is used in Layer2 mode to support `LoadBalancer` type services in a bare-metal environment, eliminating the need for a hardware load balancer.

#### 5.4. Ingress and Gateway API: Traffic Management

Two Ingress controllers are used in StreamForge for managing incoming traffic, ensuring flexible routing and fault tolerance:

- **Traefik** (v36.1.0) — the primary Ingress controller, utilizing the new **Gateway API** for declarative routing and traffic management at L7 (HTTP/HTTPS) and L4 (TCP/UDP) layers.
- **ingress-nginx** (v4.12.1) — a backup Ingress controller, providing compatibility and additional fault tolerance.

Settings include:
- TLS via `cert-manager` and internal CA `homelab-ca-issuer`
- External IP: `192.168.1.153`
- ACME storage: 1Gi NFS
- Monitoring via `/dashboard`
- Support for TCP services (`ssh`, `kafka`)

#### 5.5. DNS and TLS

- **Technitium DNS Server** provides a local resolver with support for arbitrary DNS zones, including `*.dmz.home`, ensuring access to services by human-readable names.
- **cert-manager** automates TLS certificate management, reducing the risk of errors and enhancing the security of communications between components.

##### `script.sh` for TLS Certificate Generation

The `/platform/base/cert/script.sh` script automates the TLS certificate creation cycle, including:
1. Configuration of generation and storage parameters;
2. Creation of CSR with SAN fields (FQDN + IP);
3. Formation of a `CertificateRequest` resource and submission to `cert-manager`;
4. Waiting for execution and saving PEM files;
5. Certificate validation using `openssl`.

---

### Chapter 6: Data Management: Storage and Access Strategies

Persistent data storage is a critically important aspect for ensuring long-term analytics and effective model training. In StreamForge, data storage is segmented by functional zones to optimize performance and availability.

#### 6.1. Overview of Storage Solutions

- **Linstor Piraeus** — a fault-tolerant block storage (RWO) for critical services such as PostgreSQL and ArangoDB, ensuring high availability and data integrity.
- **GlusterFS** and **NFS Subdir External Provisioner** (v4.0.18) — used to provide shared volumes with RWX (ReadWriteMany) mode, which is ideal for JupyterHub and shared data. The main access path: `192.168.1.6:/data0/k2`.

#### 6.2. Object Storage Minio

**Minio** — an S3-compatible object storage, used for:
- storing model artifacts (GNN, PPO),
- backing up services and metadata.

Ensures high availability and integration with Kubernetes via StatefulSet.

---

### Chapter 7: Data Platform: Information Management

#### 7.1. Strimzi Kafka Operator

**Strimzi** provides a full lifecycle management for Apache Kafka in a Kubernetes environment, including deployment, updates, topic configuration, encryption, and monitoring. Integration is achieved through `KafkaUser`, `KafkaTopic`, and `KafkaConnect` resources.

#### 7.2. ArangoDB: Multi-Model Database

ArangoDB is a multi-model database that effectively combines document- and graph-oriented data models within a single engine:
- **Documents**: used for storing historical candles and events, providing flexibility and scalability.
- **Graphs**: applied to describe complex relationships between assets and trading operations, which is critically important for the functioning of Graph Neural Networks (GNN).

#### 7.3. PostgreSQL (Zalando Operator)

**Zalando Operator** ensures the deployment and management of PostgreSQL clusters with high availability, automatic backup, and failover mechanisms. This solution is used for storing structured tables containing information about Return on Investment (ROI), agent action logs, and metadata about experiments.

#### 7.4. Autoscaling with KEDA

**KEDA** (Kubernetes Event-driven Autoscaling) is a component that dynamically scales the number of consumer pods based on the volume of messages in Apache Kafka. This ensures optimal adaptation to peak and low loads without the need for manual intervention, leading to reduced operational costs and minimized idle time.

#### 7.5. Kafka UI

**Kafka UI** is a web interface developed by `provectuslabs` that provides intuitive visual control over topics, consumer groups, users, and messages in Apache Kafka.

Parameters:
- Access at `https://kafka-ui.dmz.home`
- Integration via SASL_SSL (SCRAM-SHA-512)
- Connection to cluster `k3`
- Running on `k2w-7`, 1 replica

---

### Chapter 8: Monitoring and Observability: Comprehensive System Control

To ensure stable operation and prompt incident response, StreamForge implements a comprehensive monitoring and observability system.

#### 8.1. Metrics: Prometheus, NodeExporter, cAdvisor

- **Prometheus** — a time-series collection and storage system used for aggregating system and application metrics.
- **cAdvisor** — a tool for monitoring container resources and performance.
- **NodeExporter** — an exporter for operating system and host metrics.

Components:
- kube-prometheus-stack `v71.1.0`
- TLS + Ingress for Prometheus (`prometheus.dmz.home`) and Grafana (`grafana.dmz.home`)
- Persistent volumes: Prometheus — 20Gi, Grafana — 1Gi

#### 8.2. Logs: Fluent-bit, Elasticsearch, Kibana

The **EFK stack** (Elasticsearch, Fluent-bit, Kibana) is used for centralized collection, routing, and analysis of logs in the StreamForge system:

- **Fluent-bit** applies a Lua filter for dynamic index creation based on tags (e.g., `internal-myapp-2025.08.07`), providing flexibility in log indexing.
- **Elasticsearch** provides full-text search, aggregations, and log storage.
- **Kibana** visualizes logs, offering a convenient interface for analysis by tags, indices, and time ranges.

#### 8.3. Grafana and Alertmanager

- **Grafana** — a data visualization platform integrated with Prometheus, Elasticsearch, and PostgreSQL for a comprehensive view of metrics and logs.
- **Alertmanager** — a component responsible for routing and sending alerts via email and Telegram based on defined rules.

---

### Chapter 9: Automation and GitOps: Optimizing Deployment Processes

StreamForge implements a GitOps approach that automates and simplifies deployment and infrastructure management processes, minimizing manual intervention and increasing reliability.

#### 9.1. GitLab Runner

The CI/CD pipeline is built on GitLab CI and uses `kaniko` for secure container image building without the need for a Docker Daemon.

- The Runner operates in a `kubernetes` executor with a `nodeSelector` on node `k2w-9` for optimal resource distribution.
- Minio-based caching is supported to speed up the build process.
- CI/CD configuration is divided into common templates (`.build_python_service`) and specific pipelines for each service, ensuring modularity and reusability.

##### 9.1.1. Runner: Configuration Features

- Privileged rights
- ServiceAccount: `full-access-sa`
- Pools: `runner-home`, `docker-config`, `home-certificates`
- Repository: `https://gitlab.dmz.home/`

##### 9.1.2. Pipeline Structure

- `setup` → `build` → `test` → `deploy`
- Include files with paths to services are used
- Reusable templates `.gitlab/ci-templates/`

##### 9.1.3. Integration and Modularity

Each service (e.g., `dummy-service`) uses `SERVICE_NAME`, `SERVICE_PATH` variables and extends a common template.

#### 9.2. ArgoCD

**ArgoCD** is a declarative GitOps tool designed for automated management of Kubernetes cluster state based on a Git repository. It provides:

- **Single Source of Truth:** The `iac_kubeadm` repository (`gitlab.dmz.home`) serves as the single source of truth for cluster configuration.
- **TLS Support:** Secure communication with GitLab is ensured via TLS.
- **Web Access:** Access to the ArgoCD user interface is available at `argocd.dmz.home`.

- **Version Control:** All infrastructure components are under version control, simplifying change tracking and rollback to previous states.

#### 9.3. Reloader

**Reloader** is a utility that ensures automatic reloading of pods in Kubernetes when associated `Secret` or `ConfigMap` objects change. This guarantees that applications always use the latest configuration without manual intervention, maintaining consistency of deployed components.

---

### Chapter 10: Security and Additional Capabilities

#### 10.1. HashiCorp Vault

**HashiCorp Vault** is used in combination with the `Vault CSI Driver` for secure and dynamic delivery of temporary secrets to Kubernetes pods, preventing their persistent storage within the cluster.

#### 10.2. Keycloak

**Keycloak** is a unified authentication and access management (IAM) server for all platform services. It supports SSO (Single Sign-On) and OpenID Connect standards, and integrates with Grafana, Kibana, and ArgoCD for centralized user and permission management.

#### 10.3. NVIDIA GPU Operator

**NVIDIA GPU Operator** automatically detects and configures GPUs in a Kubernetes cluster, eliminating the need for manual driver installation.

- Version: `v24.9.2`
- GNN Training Support: Provides the necessary infrastructure for efficient Graph Neural Network training.
- Easy Updates via Helm: Simplifies the process of updating and managing the operator.

#### 10.4. Other Utilities

- `kubed` — a utility for synchronizing configurations between namespaces in Kubernetes, ensuring configuration consistency.
- `Mailrelay` — a centralized SMTP bus used for sending notifications from various system components, such as Alertmanager, CronJobs, and CI/CD pipelines.
