FROM registry.dmz.home/streamforge/core-modules/python:3.11-alpine

WORKDIR /app

# Установка зависимостей
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev \
    bash zlib-dev libc-dev linux-headers && \
    pip install --no-cache-dir aiokafka loguru python-dotenv

COPY . /app

CMD ["python", "main.py"]


