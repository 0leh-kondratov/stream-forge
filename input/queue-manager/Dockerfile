# syntax=docker/dockerfile:1

FROM python:3.11-alpine

# Установка зависимостей
RUN apk update && apk add --no-cache \
    gcc musl-dev libffi-dev openssl-dev python3-dev build-base

# Рабочая директория
WORKDIR /app

# Копирование зависимостей и установка
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Переменные среды
ENV PYTHONUNBUFFERED=1

# Запуск
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]