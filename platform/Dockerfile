FROM registry.dmz.home/kinga/stream-forge/python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1     SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt     REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# Install common system dependencies if needed

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

# Copy and install dev-ca.crt to system's trusted CA store
COPY ca.crt /usr/local/share/ca-certificates/dev-ca.crt
RUN update-ca-certificates

# Copy and install common Python and test dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy and install our common library via wheel
COPY libs /tmp/libs
RUN pip install --no-cache-dir /tmp/libs/streamforge_utils && rm -rf /tmp/libs

WORKDIR /app
