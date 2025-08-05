FROM registry.dmz.home/streamforge/core-modules/python:3.11-alpine

WORKDIR /app

# Установка зависимостей
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev \
    bash zlib-dev libc-dev linux-headers && \
    pip install --no-cache-dir aiokafka loguru python-dotenv

COPY . /app

CMD ["python", "main.py"]


# Dockerfile
FROM python:3.11-slim

# Установим зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gcc && \
    rm -rf /var/lib/apt/lists/*

# Установим Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . /app
WORKDIR /app

# Установим переменные среды
ENV PYTHONUNBUFFERED=1
ENV TZ=UTC

# Команда по умолчанию
CMD ["python3.11", "main.py"]
