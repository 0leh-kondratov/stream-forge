# StreamForge: Innovative Platform for Cryptocurrency Data Processing

This document provides a comprehensive description of the **StreamForge** project—an advanced platform designed for highly efficient collection, comprehensive processing, and in-depth analysis of cryptocurrency data in real-time. The project is developed using modern Cloud Native technologies and architectural patterns, ensuring scalability, reliability, and flexibility of the solution.

## 1.1. Cryptocurrency Data: Challenges and Solutions

In the contemporary landscape of digital assets, cryptocurrency data serves as a fundamental basis for analytical processes and real-time decision-making. Characteristic features of this data include high volatility, continuous availability, and significant volumes of transactions and state updates (e.g., order book dynamics, high-frequency trading operations, time series aggregation). This imposes increased demands on the methodologies for their collection, processing, and extraction of valuable information, emphasizing the need for creating reliable and high-performance data pipelines.

Key challenges include:
- **Diversity of Sources:** Data originates from various points via REST APIs for historical data and WebSockets for real-time data, requiring the integration of heterogeneous streams.
- **Scalability and Speed:** The system must withstand extreme loads, processing intensive data streams without delays.
- **Reliability:** Guaranteeing data integrity and rapid recovery after potential failures.
- **Orchestration Complexity:** Effective coordination of complex task sequences is necessary, such as "load -> save -> graph building -> model training."

## 1.2. StreamForge: An Event-Driven Platform

StreamForge represents an innovative event-driven platform designed for highly efficient data processing. A fundamental architectural principle is decentralized interaction between components, eliminating direct service calls. All inter-service communication occurs via the powerful message broker **Apache Kafka**. Each microservice publishes its generated data to the common bus, while other services subscribe to the topics of interest. This paradigm ensures exceptional flexibility, autonomy, and interchangeability of system components. Task orchestration is implemented through `queue-manager`, which dynamically activates the corresponding modules to perform specified operations.

The application of this approach guarantees high scalability, adaptability to changing requirements, and increased fault tolerance of the entire system.

## 1.3. Project Mission

1.  **Creation of a Unified Data Source:** Consolidating the processes of collecting, verifying, and storing market data to ensure prompt and convenient access to high-quality information.
2.  **Formation of an Innovative Environment for Data Science:** Providing a specialized platform for the development, testing, and validation of analytical models, including advanced Graph Neural Network (GNN) architectures.
3.  **Building a Reliable Foundation for Algorithmic Trading:** Developing a high-performance and fault-tolerant data pipeline, critically important for the functioning of automated trading systems.
4.  **Comprehensive Process Automation:** Minimizing manual intervention at all stages of the data lifecycle, from collection to analytical processing, to enhance operational efficiency.

## 1.4. Practical Use Cases

- **Scenario 1: Model Training on Historical Data.**
  - **Objective:** Train a GNN model on retrospective transaction data and aggregated 5-minute candles for the `BTCUSDT` trading pair over the last monthly period.
  - **Method:** A full data processing cycle is activated via `queue-manager`. Tasks are executed by Kubernetes Jobs: `loader-producer` loads data into Apache Kafka, `arango-connector` ensures its persistent storage in ArangoDB, `graph-builder` forms the graph structure, and `gnn-trainer` performs model training.

- **Scenario 2: Real-time Market Monitoring.**
  - **Objective:** Obtain streaming data on transactions and order book state in real-time for the `ETHUSDT` trading pair.
  - **Method:** The `loader-ws` module establishes a connection with WebSocket and transmits data to Apache Kafka. The developing visualization module subscribes to the relevant topics to display data on an interactive dashboard.

- **Scenario 3: Rapid Data Analysis.**
  - **Objective:** Verify a hypothesis regarding the correlation between trading volumes and market volatility.
  - **Method:** Using `Jupyter Server` to establish a connection with ArangoDB and conduct analytical research based on data already aggregated and processed by the StreamForge system.

These powerful functionalities make StreamForge an indispensable tool for anyone striving for maximum efficiency in working with cryptocurrency data.

# StreamForge Table of Contents

- [StreamForge: Overview](README.md)
    - [1.1. Cryptocurrency Data: Challenges and Solutions](#11-cryptocurrency-data-challenges-and-solutions)
    - [1.2. StreamForge: An Event-Driven Platform](#12-streamforge-an-event-driven-platform)
    - [1.3. Project Mission](#13-project-mission)
    - [1.4. Practical Use Cases](#14-practical-use-cases)

- [Part II: Architecture and Functioning](StreamForge_II_Architecture_and_Functioning.md)
    - [Chapter 2: High-Level Architecture](StreamForge_II_Architecture_and_Functioning.md#chapter-2-high-level-architecture)
        - [2.1. Core Architectural Principles](StreamForge_II_Architecture_and_Functioning.md#21-core-architectural-principles)
        - [2.2. Data Flow in the System](StreamForge_II_Architecture_and_Functioning.md#22-data-flow-in-the-system)
    - [Chapter 3: Apache Kafka as a Central Component](StreamForge_II_Architecture_and_Functioning.md#chapter-3-apache-kafka-as-a-central-component)
        - [Topic "queue-control"](StreamForge_II_Architecture_and_Functioning.md#topic-queue-control)
        - [Topic "queue-events"](StreamForge_II_Architecture_and_Functioning.md#topic-queue-events)
    - [Chapter 4: Microservices](StreamForge_II_Architecture_and_Functioning.md#chapter-4-microservices)
        - [4.1. queue-manager: Central Control Component](StreamForge_II_Architecture_and_Functioning.md#41-queue-manager-central-control-component)
        - [4.2. Data Collection: loader-*: Modules for Data Ingestion](StreamForge_II_Architecture_and_Functioning.md#42-data-collection-loader-modules-for-data-ingestion)
        - [4.3. Data Storage: arango-connector — Persistence Component](StreamForge_II_Architecture_and_Functioning.md#43-data-storage-arango-connector-persistence-component)
        - [4.4. Analytical Layer: graph-builder and gnn-trainer — Analytics and Machine Learning Core](StreamForge_II_Architecture_and_Functioning.md#44-analytical-layer-graph-builder-and-gnn-trainer-analytics-and-machine-learning-core)
        - [4.5. dummy-service: Auxiliary Tool for Testing](StreamForge_II_Architecture_and_Functioning.md#45-dummy-service-auxiliary-tool-for-testing)

- [Part III: Infrastructure and Environment](StreamForge_III_Infrastructure_and_Environment.md)
    - [Chapter 5: Platform Fundamentals: Kubernetes and Virtualization](StreamForge_III_Infrastructure_and_Environment.md#chapter-5-platform-fundamentals-kubernetes-and-virtualization)
        - [5.1. Foundation: Proxmox VE](StreamForge_III_Infrastructure_and_Environment.md#51-foundation-proxmox-ve)
        - [5.2. Cluster Deployment: Kubespray](StreamForge_III_Infrastructure_and_Environment.md#52-cluster-deployment-kubespray)
        - [5.3. Network Infrastructure](StreamForge_III_Infrastructure_and_Environment.md#53-network-infrastructure)
        - [5.4. Ingress and Gateway API: Traffic Management](StreamForge_III_Infrastructure_and_Environment.md#54-ingress-and-gateway-api-traffic-management)
        - [5.5. DNS and TLS](StreamForge_III_Infrastructure_and_Environment.md#55-dns-and-tls)
            - [`script.sh` for TLS Certificate Generation](StreamForge_III_Infrastructure_and_Environment.md#scriptsh-for-tls-certificate-generation)
    - [Chapter 6: Data Management: Storage and Access Strategies](StreamForge_III_Infrastructure_and_Environment.md#chapter-6-data-management-storage-and-access-strategies)
        - [6.1. Overview of Storage Solutions](StreamForge_III_Infrastructure_and_Environment.md#61-overview-of-storage-solutions)
        - [6.2. Object Storage Minio](StreamForge_III_Infrastructure_and_Environment.md#62-object-storage-minio)
    - [Chapter 7: Data Platform: Information Management](StreamForge_III_Infrastructure_and_Environment.md#chapter-7-data-platform-information-management)
        - [7.1. Strimzi Kafka Operator](StreamForge_III_Infrastructure_and_Environment.md#71-strimzi-kafka-operator)
        - [7.2. ArangoDB: Multi-Model Database](StreamForge_III_Infrastructure_and_Environment.md#72-arangodb-multi-model-database)
        - [7.3. PostgreSQL (Zalando Operator)](StreamForge_III_Infrastructure_and_Environment.md#73-postgresql-zalando-operator)
        - [7.4. Autoscaling with KEDA](StreamForge_III_Infrastructure_and_Environment.md#74-autoscaling-with-keda)
        - [7.5. Kafka UI](StreamForge_III_Infrastructure_and_Environment.md#75-kafka-ui)
    - [Chapter 8: Monitoring and Observability: Comprehensive System Control](StreamForge_III_Infrastructure_and_Environment.md#chapter-8-monitoring-and-observability-comprehensive-system-control)
        - [8.1. Metrics: Prometheus, NodeExporter, cAdvisor](StreamForge_III_Infrastructure_and_Environment.md#81-metrics-prometheus-nodeexporter-cadvisor)
        - [8.2. Logs: Fluent-bit, Elasticsearch, Kibana](StreamForge_III_Infrastructure_and_Environment.md#82-logs-fluent-bit-elasticsearch-kibana)
        - [8.3. Grafana and Alertmanager](StreamForge_III_Infrastructure_and_Environment.md#83-grafana-and-alertmanager)
    - [Chapter 9: Automation and GitOps: Optimizing Deployment Processes](StreamForge_III_Infrastructure_and_Environment.md#chapter-9-automation-and-gitops-optimizing-deployment-processes)
        - [9.1. GitLab Runner](StreamForge_III_Infrastructure_and_Environment.md#91-gitlab-runner)
            - [9.1.1. Runner: Configuration Features](StreamForge_III_Infrastructure_and_Environment.md#911-runner-configuration-features)
            - [9.1.2. Pipeline Structure](StreamForge_III_Infrastructure_and_Environment.md#912-pipeline-structure)
            - [9.1.3. Integration and Modularity](StreamForge_III_Infrastructure_and_Environment.md#913-integration-and-modularity)
        - [9.2. ArgoCD](StreamForge_III_Infrastructure_and_Environment.md#92-argocd)
        - [9.3. Reloader](StreamForge_III_Infrastructure_and_Environment.md#93-reloader)
    - [Chapter 10: Security and Additional Capabilities](StreamForge_III_Infrastructure_and_Environment.md#chapter-10-security-and-additional-capabilities)
        - [10.1. HashiCorp Vault](StreamForge_III_Infrastructure_and_Environment.md#101-hashicorp-vault)
        - [10.2. Keycloak](StreamForge_III_Infrastructure_and_Environment.md#102-keycloak)
        - [10.3. NVIDIA GPU Operator](StreamForge_III_Infrastructure_and_Environment.md#103-nvidia-gpu-operator)
        - [10.4. Other Utilities](StreamForge_III_Infrastructure_and_Environment.md#104-other-utilities)

- [Part IV: Future Prospects: StreamForge Roadmap](StreamForge_IV_What_Next_My_Development_Plans.md)
    - [Chapter 11: Self-Healing Engine: Automated Functionality Recovery](StreamForge_IV_What_Next_My_Development_Plans.md#chapter-11-self-healing-engine-automated-functionality-recovery)
    - [Chapter 12: Chaos Engineering: System Resilience Verification](StreamForge_IV_What_Next_My_Development_Plans.md#chapter-12-chaos-engineering-system-resilience-verification)
    - [Chapter 13: Progressive Delivery: Safe Deployment Strategies](StreamForge_IV_What_Next_My_Development_Plans.md#chapter-13-progressive-delivery-safe-deployment-strategies)

- [Part V: Technical Details and Appendices](StreamForge_V_Technical_Details_and_Appendices.md)
    - [Appendix A: Data Schemas and API](StreamForge_V_Technical_Details_and_Appendices.md#appendix-a-data-schemas-and-api)
    - [Appendix B: Kubernetes Manifest Examples](StreamForge_V_Technical_Details_and_Appendices.md#appendix-b-kubernetes-manifest-examples)
        - [Example: Kubernetes Job for arango-candles](StreamForge_V_Technical_Details_and_Appendices.md#example-kubernetes-job-for-arango-candles)
    - [Appendix C: CI/CD Pipeline Examples](StreamForge_V_Technical_Details_and_Appendices.md#appendix-c-cicd-pipeline-examples)
    - [Appendix D: Glossary of Terms](StreamForge_V_Technical_Details_and_Appendices.md#appendix-d-glossary-of-terms)
    - [Appendix E: Deployment and Operations Guide](StreamForge_V_Technical_Details_and_Appendices.md#appendix-e-deployment-and-operations-guide)
    - [Appendix F: Testing Procedure](StreamForge_V_Technical_Details_and_Appendices.md#appendix-f-testing-procedure)
    - [Appendix G: Kafka Resource Management](StreamForge_V_Technical_Details_and_Appendices.md#appendix-g-kafka-resource-management)
    - [Appendix H: Kubernetes Debugging Environment](StreamForge_V_Technical_Details_and_Appendices.md#appendix-h-kubernetes-debugging-environment)
