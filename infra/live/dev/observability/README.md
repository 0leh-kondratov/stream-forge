# Grafana Alloy Observability Module for GKE Autopilot

This Terraform module deploys and configures a comprehensive observability stack on a Google Kubernetes Engine (GKE) Autopilot cluster, primarily leveraging **Grafana Alloy** for metrics and logs collection, and optionally **kube-state-metrics**. It is designed to forward all collected telemetry data to **Grafana Cloud**.

## Features

*   **Dedicated Namespace:** Deploys all observability components into a dedicated Kubernetes namespace (`observability` by default).
*   **Kube-State-Metrics (Optional):** Installs `kube-state-metrics` for rich Kubernetes cluster-state metrics.
*   **Grafana Alloy Deployment:**
    *   Uses the `alloy` Helm chart with a `deployment` controller for Autopilot compatibility.
    *   Configures resource requests and limits for efficient operation.
    *   Applies security best practices with `podSecurityContext` and `containerSecurityContext`.
*   **Comprehensive Telemetry Collection:**
    *   **Metrics:** Discovers Kubernetes services and pods, scrapes Prometheus-compatible endpoints (including `kube-state-metrics`), and forwards them to Grafana Cloud Prometheus via remote write.
    *   **Logs:** Collects Kubernetes pod logs and cluster events via the Kubernetes API, processes them, and forwards them to Grafana Cloud Loki.
    *   **Traces (Optional):** Configurable to receive OpenTelemetry Protocol (OTLP) traces and forward them to Grafana Tempo.
*   **Grafana Cloud Integration:** Seamlessly integrates with Grafana Cloud for centralized monitoring, logging, and tracing.

## Prerequisites

Before deploying this module, ensure you have the following:

*   **GKE Autopilot Cluster:** An existing GKE Autopilot cluster. This module connects to an existing cluster.
*   **Terraform:** Version `1.6.0` or higher.
*   **`gcloud` CLI:** Authenticated and configured for your GCP project.
*   **`kubectl` CLI:** Configured to connect to your GKE cluster.
*   **Grafana Cloud Account:** Access to a Grafana Cloud account with Prometheus, Loki, and (optionally) Tempo instances. You will need:
    *   Prometheus remote write endpoint, username (instance ID), and API key.
    *   Loki endpoint, username (tenant ID), and API key.
    *   Tempo OTLP endpoint and API token (if enabling traces).

## Deployment

1.  **Clone the repository (if you haven't already):**

    ```bash
    git clone <your-repo-url>
    cd <your-repo-url>/infra/live/dev/observability
    ```

2.  **Configure Terraform Variables:**

    Create a `terraform.tfvars` file in the `infra/live/dev/observability/` directory with your specific values. An example `terraform.tfvars` might look like this:

    ```terraform
    project_id                             = "your-gcp-project-id"
    region                                 = "us-central1"
    cluster_name                           = "your-gke-cluster-name"
    observability_namespace                = "observability"
    install_kube_state_metrics             = true

    # Grafana Cloud Prometheus
    grafana_cloud_prometheus_remote_write_endpoint = "https://prometheus-prod-XX.grafana.net/api/prom"
    grafana_cloud_prometheus_user          = "your-prometheus-instance-id"
    grafana_cloud_prometheus_api_key       = "your-prometheus-api-key"

    # Grafana Cloud Loki
    grafana_cloud_loki_endpoint            = "https://logs-prod-XXX.grafana.net"
    grafana_cloud_loki_user                = "your-loki-tenant-id"
    grafana_cloud_loki_api_key             = "your-loki-api-key"

    # Grafana Tempo (Optional - uncomment and fill if enabling traces)
    # grafana_tempo_otlp_endpoint          = "https://tempo-prod-<region>.grafana.net:443"
    # grafana_tempo_token                  = "your-tempo-api-token"
    ```

    **Note:** Ensure your API keys have `metrics:write`, `logs:write`, and `traces:write` permissions as appropriate.

3.  **Initialize Terraform:**

    ```bash
    terraform init
    ```

4.  **Review and Apply Changes:**

    ```bash
    terraform plan
    terraform apply
    ```

    Terraform will show you the planned changes. Type `yes` to confirm and apply the configuration.

## Testing and Verification

After successful deployment, you can verify the observability setup:

1.  **Check Kubernetes Resources:**

    Verify that the `observability` namespace, `kube-state-metrics` (if enabled), and `alloy-manual` deployments and pods are running:

    ```bash
    kubectl get ns observability
    kubectl get all -n observability
    ```

2.  **Verify Alloy Pod Logs:**

    Check the logs of the Alloy pod to ensure it's discovering targets and sending data without errors:

    ```bash
    kubectl logs -f -n observability deploy/alloy-manual
    ```

3.  **Check Metrics in Grafana Cloud:**

    *   Log in to your Grafana Cloud account.
    *   Navigate to **Explore**.
    *   Select your **Prometheus** data source.
    *   Run a query like `up` or `kube_pod_info` (if kube-state-metrics is enabled) to see if metrics are flowing.
    *   You can also try `topk(5, up)` or `label_values(up, cluster)` as suggested in the Terraform outputs.

4.  **Check Logs in Grafana Cloud:**

    *   Log in to your Grafana Cloud account.
    *   Navigate to **Explore**.
    *   Select your **Loki** data source.
    *   Run a query like `{cluster="<your-cluster-name>"}` or `{job="kubernetes-pods"}` to see if logs are flowing from your GKE cluster.
    *   You should see logs from your `sample-logger-py` application if it's deployed and generating logs.

5.  **Check Traces in Grafana Cloud (if enabled):**

    *   Log in to your Grafana Cloud account.
    *   Navigate to **Explore**.
    *   Select your **Tempo** data source.
    *   Search for traces generated by your applications (e.g., `sample-logger-py` if it's configured to send traces).

## Cleanup

To destroy the resources deployed by this module:

```bash
cd infra/live/dev/observability
terraform destroy
```

**Note:** This will only destroy resources managed by this specific Terraform module. Your GKE cluster itself will not be destroyed.
