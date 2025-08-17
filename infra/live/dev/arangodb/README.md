# ArangoDB on GKE Autopilot (Terraform)

This module installs ArangoDB Operator + CRDs via Helm and creates an `ArangoDeployment` (Single by default) with CSI-backed PVCs on `standard-rwo`.

## Prereqs
- Existing GKE Autopilot cluster
- `gcloud auth application-default login`
- Terraform >= 1.6
- Project ID and region
- (Optional) HTTP backend config

## Init
```bash
terraform -chdir=infra/live/dev/arangodb init \
  -reconfigure \
  -backend-config="address=https://YOUR_GITLAB/api/v4/projects/ID/terraform/state/arangodb" \
  -backend-config="lock_address=..." \
  -backend-config="unlock_address=..." \
  -backend-config="lock_method=POST" \
  -backend-config="unlock_method=DELETE" \
  -backend-config="username=YOUR_USER" \
  -backend-config="password=glpat-YOUR_TOKEN"
