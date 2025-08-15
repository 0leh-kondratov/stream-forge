## Introduction

This Terraform configuration deploys a Google Kubernetes Engine (GKE) Autopilot cluster in Google Cloud Platform (GCP). It creates a custom VPC, subnet with secondary ranges for pods and services, enables required APIs, and sets up a regional Autopilot cluster. The setup is minimalistic and cost-effective by default, suitable for development environments.

**Note:** GKE Autopilot manages node pools automatically; do not manually create resources in the `kube-system` namespace, as it is managed by GKE.

## Prerequisites

- A Google Cloud Platform (GCP) account with a billing account enabled (even for free tier usage; check GCP Free Tier limits).
- Terraform installed (version >= 1.6).
- Google Cloud SDK (`gcloud`) installed and authenticated with `gcloud auth login`.
- kubectl installed for Kubernetes interactions.
- A GCP project ID (set in `terraform.tfvars`).

## Directory Structure

The configuration files are located in `infra/live/dev/gke/`:

- `versions.tf`: Specifies Terraform and provider versions.
- `variables.tf`: Defines input variables with defaults.
- `providers.tf`: Configures the Google provider.
- `apis.tf`: Enables required GCP APIs.
- `network.tf`: Creates VPC and subnet.
- `cluster.tf`: Deploys the GKE Autopilot cluster.
- `outputs.tf`: Defines outputs like cluster name and connection hints.
- `terraform.tfvars`: Example variable values (customize with your project ID).

## Installation and Deployment

1. **Clone or Create the Repository:**
   Create the directory structure and place the `.tf` files as provided.

2. **Initialize Terraform:**
   ```
   terraform -chdir=infra/live/dev/gke init
   ```

3. **Review the Plan:**
   ```
   terraform -chdir=infra/live/dev/gke plan
   ```

4. **Apply the Configuration:**
   ```
   terraform -chdir=infra/live/dev/gke apply -auto-approve
   ```
   This will create the VPC, enable APIs, and deploy the GKE cluster. Monitor the output for any errors.

## Usage

After deployment, Terraform will output:
- `cluster_name`: The name of the GKE cluster.
- `cluster_region`: The region of the cluster.
- `get_credentials_hint`: A ready-to-use `gcloud` command to configure kubectl.

Example outputs:
```
cluster_name = "gke-free-autopilot"
cluster_region = "us-central1"
get_credentials_hint = "gcloud container clusters get-credentials gke-free-autopilot --region us-central1 --project stream-forge-4"
```

## Accessing the Cluster

1. **Configure kubectl:**
   Run the command from the `get_credentials_hint` output to update your local kubeconfig:
   ```
   gcloud container clusters get-credentials ${cluster_name} --region ${cluster_region} --project ${project_id}
   ```
   Replace placeholders with actual values.

2. **Verify Access:**
   ```
   kubectl get nodes
   ```
   This should list the Autopilot-managed nodes.

3. **Interact with the Cluster:**
   Use `kubectl` commands to deploy applications, manage resources, etc.

## Smoke Test

To verify the cluster is working:

1. Save the following YAML as `smoke-test.yaml`:
   ```
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: smoke-test-nginx
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: nginx
     template:
       metadata:
         labels:
           app: nginx
       spec:
         containers:
         - name: nginx
           image: nginx:alpine
           resources:
             requests:
               cpu: "100m"
               memory: "128Mi"
             limits:
               cpu: "100m"
               memory: "128Mi"
           ports:
           - containerPort: 80
   ---
   apiVersion: v1
   kind: Service
   metadata:
     name: smoke-test-nginx
   spec:
     type: ClusterIP
     selector:
       app: nginx
     ports:
     - port: 80
       targetPort: 80
   ```

2. Apply the manifest:
   ```
   kubectl apply -f smoke-test.yaml
   ```

3. Port-forward to access locally:
   ```
   kubectl port-forward svc/smoke-test-nginx 8080:80
   ```
   Open http://localhost:8080 in a browser to see the nginx welcome page. Press Ctrl+C to stop.

4. Clean up:
   ```
   kubectl delete -f smoke-test.yaml
   ```

## Cleanup

To destroy the resources:
```
terraform -chdir=infra/live/dev/gke destroy -auto-approve
```
## Outputs:

```
cluster_name = "gke-free-autopilot"
cluster_region = "us-central1"
get_credentials_hint = "gcloud container clusters get-credentials gke-free-autopilot --region us-central1 --project stream-forge-4"
```