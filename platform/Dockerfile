# Base image based on the official Python 3.11 slim version
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        curl \
        gnupg \
        git \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip (you can optionally install poetry or any global tools here)
RUN pip install --upgrade pip

# Default command
CMD ["python"]

