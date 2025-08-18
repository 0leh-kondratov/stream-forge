#!/usr/bin/env bash
set -euo pipefail
# Label StreamForge worker nodes
kubectl label node k2w-7 streamforge-node=true --overwrite
kubectl label node k2w-8 streamforge-node=true --overwrite
kubectl label node k2w-9 streamforge-node=true --overwrite
