#!/bin/bash
# Variables
NAMESPACE="default"          # Namespace cert-manager
CERT_NAME="technitium-dmz-tls" # Certificate name
DOMAIN0="technitium.dmz.home" # Domain for certificate
IP_ADDRESS="192.168.1.92"  # IP address for certificate
DURATION=87600               # Validity period (10 years)
OUTPUT_DIR="./certs"         # Directory for saving files

# Create directory for saving certificates if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Paths for temporary files
CSR_FILE="$OUTPUT_DIR/${CERT_NAME}.csr"
KEY_FILE="$OUTPUT_DIR/${CERT_NAME}.key"

# Create private key
openssl genrsa -out "$KEY_FILE" 4096

# Create CSR with SAN (Subject Alternative Name)
openssl req -new -sha512 -key "$KEY_FILE" -out "$CSR_FILE" -subj "/CN=$DOMAIN0" \
  -addext "subjectAltName=DNS:$DOMAIN0,IP:$IP_ADDRESS"


# Encode CSR in Base64
CSR_BASE64=$(cat "$CSR_FILE" | base64 | tr -d '\n')

# Create CertificateRequest YAML and apply it
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: CertificateRequest
metadata:
  name: ${CERT_NAME}-request
  namespace: $NAMESPACE
spec:
  request: $CSR_BASE64
  duration: ${DURATION}h
  usages:
  - digital signature
  - key encipherment
  issuerRef:
    kind: ClusterIssuer
    name: k3s-ca-issuer
EOF

echo "CertificateRequest created. Waiting for execution..."

# Waiting for CertificateRequest execution
for i in {1..30}; do
  STATUS=$(kubectl get certificaterequest ${CERT_NAME}-request -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)
  if [[ "$STATUS" == "True" ]]; then
    echo "CertificateRequest executed successfully."
    break
  fi
  echo "Waiting for CertificateRequest execution..."
  sleep 10
done

# Check if certificate was created
CERTIFICATE=$(kubectl get certificaterequest ${CERT_NAME}-request -n $NAMESPACE -o jsonpath='{.status.certificate}')
if [[ -z "$CERTIFICATE" ]]; then
  echo "Error: Certificate was not created."
  exit 1
fi

# Saving certificate to file

CERT_FILE="$OUTPUT_DIR/${CERT_NAME}.crt"

echo "$CERTIFICATE" | base64 -d > "$CERT_FILE"

echo "Certificate successfully saved:"
echo "  Certificate: $CERT_FILE"
echo "  Key: $KEY_FILE"

openssl rsa  -modulus -noout -in ${KEY_FILE}  | openssl md5
openssl x509 -modulus -noout -in ${CERT_FILE} | openssl md5
openssl verify -verbose -CAfile ${OUTPUT_DIR}/k3s.crt ${CERT_FILE}
openssl x509  -text -noout -in ${CERT_FILE}
