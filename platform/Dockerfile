FROM registry.dmz.home/kinga/stream-forge/python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1     SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt     REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# Устанавливаем общие системные зависимости, если они нужны

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем dev-ca.crt в системное хранилище доверенных сертификатов
COPY ca.crt /usr/local/share/ca-certificates/dev-ca.crt
RUN update-ca-certificates

# Устанавливаем общие Python-зависимости и тестовые зависимости
RUN pip install --no-cache-dir uvloop loguru aiokafka pytest pytest-asyncio httpx python-arango

# Копируем и устанавливаем нашу общую библиотеку через wheel
COPY libs /tmp/libs
RUN pip install --no-cache-dir /tmp/libs/streamforge_utils && rm -rf /tmp/libs

WORKDIR /app
