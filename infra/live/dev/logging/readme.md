
# EFK Stack Deployment on GKE Autopilot (Development)

This repository contains Terraform configuration for deploying a minimal **Elasticsearch + Fluent Bit + Kibana** (EFK) stack into an **existing GKE Autopilot cluster** for development and testing purposes.

> **⚠️ Warning:**  
> This setup is intended **only for development**.  
> Security is disabled (`xpack.security.enabled: false`) in Elasticsearch, Kibana is publicly accessible through port-forwarding only, and the Elasticsearch protocol is set to **HTTP** for simplicity.  
> **Do not use in production**.

---

## 📦 Components

- **Elasticsearch** (single-node)
  - Version: `8.5.1` (Helm chart)
  - Single replica, 20Gi PVC on PD-Standard
  - Security disabled for dev
- **Kibana**
  - Version: `8.5.1` (Helm chart)
  - Minimal CPU/memory requests
  - Connected to Elasticsearch via HTTP
- **Fluent Bit**
  - Version: `0.49.1` (Helm chart)
  - DaemonSet with safe hostPath mounts (`/var/log` and `/var/log/containers`, read-only)
  - Collects container logs and ships them to Elasticsearch

---

## 🚀 Deployment

### 1. Prepare Terraform

```bash
cd infra/live/dev/logging/

terraform init
terraform plan
terraform apply
````

Variables are defined in [`terraform.tfvars`](terraform.tfvars):

```hcl
project_id = "stream-forge-4"
region     = "us-central1"
cluster    = "gke-free-autopilot"
```

### 2. Wait for Pods

```bash
kubectl -n logging get pods
```

You should see:

```
NAME                                      READY   STATUS    RESTARTS   AGE
elasticsearch-master-0                    1/1     Running   0          2m
kibana-kibana-xxxxxxxxxx-yyyyy            1/1     Running   0          2m
fluent-bit-xxxxx                          1/1     Running   0          2m
```

---

## 🔌 Connecting to Kibana and Elasticsearch

### Port-forward Kibana

```bash
kubectl -n logging port-forward svc/kibana-kibana 5601:5601
```

Open in browser:

```
http://localhost:5601
```

### Port-forward Elasticsearch

```bash
kubectl -n logging port-forward svc/elasticsearch-master 9200:9200
```

Check connection:

```bash
curl http://localhost:9200
```

Expected response:

```json
{
  "name" : "elasticsearch-master-0",
  "cluster_name" : "elasticsearch",
  "cluster_uuid" : "...",
  "version" : { ... },
  "tagline" : "You Know, for Search"
}
```

---

## 📊 Creating an Index in Kibana

Once connected to Kibana:

1. **Access Kibana Dev Tools**

   * In Kibana sidebar, go to **"Dev Tools" → "Console"**

2. **Create an Index**

   ```json
   PUT my-test-index
   {
     "settings": {
       "number_of_shards": 1,
       "number_of_replicas": 0
     }
   }
   ```

   * This creates a simple index named `my-test-index`.

3. **Insert a Sample Document**

   ```json
   POST my-test-index/_doc/1
   {
     "message": "Hello EFK!",
     "timestamp": "2025-08-15T12:00:00Z"
   }
   ```

4. **Search in the Index**

   ```json
   GET my-test-index/_search
   {
     "query": {
       "match_all": {}
     }
   }
   ```

---

## 📈 Viewing Logs in Kibana (Discover)

Fluent Bit ships Kubernetes container logs to Elasticsearch automatically.

1. Go to **"Discover"** in Kibana.
2. Select the index pattern that matches container logs.

   * If using the provided config, Fluent Bit sends logs in Logstash format with index name like:

     ```
     logstash-YYYY.MM.DD
     ```
3. Create a new **Index Pattern**:

   * Pattern: `logstash-*`
   * Time filter field: `@timestamp`
4. Apply and start browsing logs in Discover.

---

## 🛠 Autopilot Notes

* All pods run with resource requests/limits compatible with **GKE Autopilot**.
* No `hostNetwork`, `hostPID`, or privileged containers are used.
* Only `/var/log` and `/var/log/containers` are mounted (read-only) in Fluent Bit.

---

## 🧹 Cleanup

To remove all resources:

```bash
terraform destroy
```

---

## 📚 Useful Commands

* Get all pods:

  ```bash
  kubectl -n logging get pods -o wide
  ```
* Port-forward Kibana:

  ```bash
  kubectl -n logging port-forward svc/kibana-kibana 5601:5601
  ```
* Port-forward Elasticsearch:

  ```bash
  kubectl -n logging port-forward svc/elasticsearch-master 9200:9200
  ```
* Test Elasticsearch:

  ```bash
  curl http://localhost:9200
  ```

