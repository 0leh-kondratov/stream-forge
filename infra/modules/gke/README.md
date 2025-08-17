# GKE Module

This directory contains a Terraform module for provisioning a Google Kubernetes Engine (GKE) cluster.

## Features

- Deploys a GKE cluster with configurable settings.
- Manages node pools, networking, and other cluster-related resources.

## Usage

To use this module, include it in your Terraform configuration:

```terraform
module "gke_cluster" {
  source = "./modules/gke"

  project_id   = var.project_id
  region       = var.region
  cluster_name = "my-gke-cluster"
  # ... other variables
}
```

## Inputs

| Name         | Description                               | Type     | Default |
|--------------|-------------------------------------------|----------|---------|
| `project_id` | The GCP project ID.                       | `string` | n/a     |
| `region`     | The GCP region for the GKE cluster.       | `string` | n/a     |
| `cluster_name` | The name of the GKE cluster.              | `string` | n/a     |
| `node_locations` | List of zones in which the cluster's nodes are located. | `list(string)` | `[]` |
| `initial_node_count` | The number of nodes in the cluster.       | `number` | `1`     |

## Outputs

| Name             | Description                               |
|------------------|-------------------------------------------|
| `cluster_name`   | The name of the created GKE cluster.      |
| `cluster_endpoint` | The endpoint of the GKE cluster.          |
| `kubeconfig`     | Kubeconfig for connecting to the cluster. |
