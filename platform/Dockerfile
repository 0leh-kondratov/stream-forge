FROM registry.dmz.home/kinga/stream-forge/python:3.11-slim

# Устанавливаем общие системные зависимости, если они нужны
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем dev-ca.crt в системное хранилище доверенных сертификатов
COPY devcontainer/dev-ca.crt /usr/local/share/ca-certificates/dev-ca.crt
RUN update-ca-certificates

# Устанавливаем общие Python-зависимости
RUN pip install uvloop loguru aiokafka

# Копируем и устанавливаем нашу общую библиотеку
COPY ./libs/streamforge_utils /app/libs/streamforge_utils
RUN pip install -e /app/libs/streamforge_utils

WORKDIR /app
