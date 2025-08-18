#!/usr/bin/env bash
set -euo pipefail

# one-prime: bootstrap k2 cluster baseline
# Requirements: kubectl, helm, cluster-admin permissions

# --- CONFIG (edit if needed) ---
METALLB_IP_POOL_START="192.168.1.116"
METALLB_IP_POOL_END="192.168.1.130"
NFS_SERVER="192.168.1.4"
NFS_PATH="/data/nfs"
LOCAL_CA_SECRET_NAME="homelab-ca"          # secret with tls.crt/tls.key (namespace: cert-manager)
ISSUER_NAME="homelab-ca-issuer"
DOMAIN_SUFFIX="dmz.home"
INGRESS_NGINX_IP="192.168.1.116"
TRAEFIK_IP="192.168.1.117"

# Namespaces
NS_INGRESS_NGINX="ingress-nginx"
NS_TRAEFIK="traefik"
NS_METALLB="metallb"
NS_CERT_MGR="cert-manager"
NS_NFS="nfs-provisioner"
NS_MONITORING="monitoring"
NS_ARGOCD="argocd"
NS_LOGGING="logging"
NS_KAFKA_STRIMZI="kafka-strimzi"
NS_GPU="gpu-operator"
NS_STF="stf"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALUES_DIR="${ROOT_DIR}/values"
MANIFESTS_DIR="${ROOT_DIR}/manifests"

echo "==> Create namespaces (idempotent)"
kubectl apply -f "${MANIFESTS_DIR}/ns.yaml"

echo "==> Label StreamForge nodes (k2w-7, k2w-8, k2w-9)"
bash "${MANIFESTS_DIR}/node-labels.sh" || true

echo "==> Add Helm repos (idempotent)"
helm repo add metallb https://metallb.github.io/metallb
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add traefik https://traefik.github.io/charts
helm repo add jetstack https://charts.jetstack.io
helm repo add nfs-subdir-external-provisioner https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

echo "==> Install/upgrade MetalLB (L2)"
helm upgrade --install metallb metallb/metallb \
  --namespace "${NS_METALLB}" --create-namespace \
  -f "${VALUES_DIR}/metallb-values.yaml" \
  --wait

echo "==> Configure MetalLB IPAddressPool and L2Advertisement"
# render on the fly with env
cat <<EOF | kubectl apply -n ${NS_METALLB} -f -
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: k2-pool
spec:
  addresses:
  - ${METALLB_IP_POOL_START}-${METALLB_IP_POOL_END}
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: k2-l2
spec:
  ipAddressPools:
  - k2-pool
EOF

echo "==> Install/upgrade ingress-nginx"
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace "${NS_INGRESS_NGINX}" --create-namespace \
  -f "${VALUES_DIR}/ingress-nginx-values.yaml" \
  --set controller.service.loadBalancerIP="${INGRESS_NGINX_IP}" \
  --wait

echo "==> Install/upgrade Traefik"
helm upgrade --install traefik traefik/traefik \
  --namespace "${NS_TRAEFIK}" --create-namespace \
  -f "${VALUES_DIR}/traefik-values.yaml" \
  --set service.spec.loadBalancerIP="${TRAEFIK_IP}" \
  --wait

echo "==> Install/upgrade cert-manager"
helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace "${NS_CERT_MGR}" --create-namespace \
  -f "${VALUES_DIR}/cert-manager-values.yaml" \
  --set installCRDs=true \
  --wait

echo "==> Ensure local CA secret exists (tls.crt/tls.key) in cert-manager ns"
# Expect user to create it beforehand; skip if exists
if ! kubectl get secret "${LOCAL_CA_SECRET_NAME}" -n "${NS_CERT_MGR}" >/dev/null 2>&1; then
  echo "ERROR: Missing secret ${LOCAL_CA_SECRET_NAME} in ${NS_CERT_MGR} (tls.crt/tls.key). Please create it and rerun."
  exit 1
fi

echo "==> Apply ClusterIssuer homelab-ca-issuer"
kubectl apply -f "${MANIFESTS_DIR}/clusterissuer-homelab.yaml"

echo "==> Install/upgrade NFS subdir external provisioner"
helm upgrade --install sc-nfs nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
  --namespace "${NS_NFS}" --create-namespace \
  -f "${VALUES_DIR}/nfs-subdir-values.yaml" \
  --set nfs.server="${NFS_SERVER}" \
  --set nfs.path="${NFS_PATH}" \
  --wait

echo "==> Install/upgrade kube-prometheus-stack"
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace "${NS_MONITORING}" --create-namespace \
  -f "${VALUES_DIR}/kube-prom-stack-values.yaml" \
  --wait

echo "==> Install/upgrade Argo CD"
helm upgrade --install argocd argo/argo-cd \
  --namespace "${NS_ARGOCD}" --create-namespace \
  -f "${VALUES_DIR}/argocd-values.yaml" \
  --wait

echo "==> (Optional) Apply example Certificate for whoami.${DOMAIN_SUFFIX}"
kubectl apply -f "${MANIFESTS_DIR}/example-certificate-whoami.yaml" || true

echo "==> Done."
echo "Check:"
echo "  kubectl get nodes"
echo "  kubectl get ingressclass"
echo "  kubectl get svc -A | egrep 'LoadBalancer|ingress'"
echo "  kubectl get clusterissuer"
echo "  kubectl get storageclass"
