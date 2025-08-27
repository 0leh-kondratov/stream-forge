# ArangoDB on GKE Autopilot

This directory contains Terraform code to deploy an ArangoDB instance on a GKE Autopilot cluster.

## Architecture

The infrastructure consists of the following components:

*   **Namespace:** A dedicated `arangodb` namespace is created for all resources.
*   **ArangoDB Operator:** The ArangoDB Operator is installed using Helm to manage the ArangoDB lifecycle.
*   **ArangoDeployment:** An `ArangoDeployment` Custom Resource is created to describe the desired state of the ArangoDB cluster (in this case, a `Single` instance).
*   **Secret:** A Kubernetes secret is created to store the `root` user's password.

## Installation

### Prerequisites

*   `terraform` (version >= 1.6) installed
*   `kubectl` installed
*   Configured access to your GKE cluster

### Deployment

1.  **Initialize Terraform:**
    ```bash
    terraform init
    ```

2.  **Create `terraform.tfvars` file:**
    Create a file named `terraform.tfvars` and specify the required variables. At a minimum, you need to provide `project_id` and `root_password`.

    ```hcl
    project_id    = "your-gcp-project-id"
    cluster_name  = "gke-free-autopilot"
    root_password = "your-super-secret-password"
    ```

3.  **Plan and Apply:**
    ```bash
    terraform plan
    terraform apply
    ```

After a successful `terraform apply`, ArangoDB will be deployed in your cluster.

## Access and Control

Access to the ArangoDB web UI and API is handled via `kubectl port-forward`.

1.  **Port-Forward:**
    Run the command provided in the Terraform output (`output "port_forward_hint"`):
    ```bash
    kubectl -n arangodb port-forward svc/arango-single 8529:8529
    ```

2.  **Access the Web UI:**
    Open `http://127.0.0.1:8529` in your web browser.

3.  **Credentials:**
    *   **Username:** `root`
    *   **Password:** The password you specified in `terraform.tfvars` (`root_password`).

    The password is also stored in the `arango-single-root` Kubernetes secret in the `arangodb` namespace. You can retrieve it with the following command:
    ```bash
    kubectl -n arangodb get secret arango-single-root -o jsonpath='{.data.password}' | base64 --decode
    ```

## Monitoring

The `ArangoDeployment` configuration has metrics enabled (`metrics: enabled: true`). You can configure your Prometheus instance to scrape metrics from the `metrics` endpoint on the ArangoDB pods.