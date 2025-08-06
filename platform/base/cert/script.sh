#!/bin/bash
# Переменные
NAMESPACE="default"          # Namespace cert-manager
CERT_NAME="technitium-dmz-tls" # Имя сертификата
DOMAIN0="technitium.dmz.home" # Домен для сертификата
IP_ADDRESS="192.168.1.92"  # IP-адрес для сертификата
DURATION=87600               # Срок действия (10 лет)
OUTPUT_DIR="./certs"         # Директория для сохранения файлов

# Создать директорию для сохранения сертификатов, если её нет
mkdir -p "$OUTPUT_DIR"

# Пути для временных файлов
CSR_FILE="$OUTPUT_DIR/${CERT_NAME}.csr"
KEY_FILE="$OUTPUT_DIR/${CERT_NAME}.key"

# Создать приватный ключ
openssl genrsa -out "$KEY_FILE" 4096

# Создать CSR с SAN (Subject Alternative Name)
openssl req -new -sha512 -key "$KEY_FILE" -out "$CSR_FILE" -subj "/CN=$DOMAIN0" \
  -addext "subjectAltName=DNS:$DOMAIN0,IP:$IP_ADDRESS"


# Закодировать CSR в Base64
CSR_BASE64=$(cat "$CSR_FILE" | base64 | tr -d '\n')

# Создать CertificateRequest YAML и применить его
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

echo "CertificateRequest создан. Ожидаем выполнения..."

# Ожидание выполнения CertificateRequest
for i in {1..30}; do
  STATUS=$(kubectl get certificaterequest ${CERT_NAME}-request -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)
  if [[ "$STATUS" == "True" ]]; then
    echo "CertificateRequest выполнен успешно."
    break
  fi
  echo "Ожидание выполнения CertificateRequest..."
  sleep 10
done

# Проверить, создался ли сертификат
CERTIFICATE=$(kubectl get certificaterequest ${CERT_NAME}-request -n $NAMESPACE -o jsonpath='{.status.certificate}')
if [[ -z "$CERTIFICATE" ]]; then
  echo "Ошибка: Сертификат не был создан."
  exit 1
fi

# Сохранение сертификата в файл

CERT_FILE="$OUTPUT_DIR/${CERT_NAME}.crt"

echo "$CERTIFICATE" | base64 -d > "$CERT_FILE"

echo "Сертификат успешно сохранён:"
echo "  Сертификат: $CERT_FILE"
echo "  Ключ: $KEY_FILE"

openssl rsa  -modulus -noout -in ${KEY_FILE}  | openssl md5
openssl x509 -modulus -noout -in ${CERT_FILE} | openssl md5
openssl verify -verbose -CAfile ${OUTPUT_DIR}/k3s.crt ${CERT_FILE}
openssl x509  -text -noout -in ${CERT_FILE}
