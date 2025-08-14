# Base image defined externally, e.g., in GitHub Actions or GitLab
ARG BASE_IMAGE=ghcr.io/0leh-kondratov/stream-forge-base:latest
FROM ${BASE_IMAGE}

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
