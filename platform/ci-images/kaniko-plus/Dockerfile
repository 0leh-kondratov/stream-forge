# Using Alpine as the base image, as it is lightweight.
FROM alpine:3.18

# Install git, curl and ca-certificates (for HTTPS)
RUN apk add --no-cache \
    git \
    curl \
    ca-certificates

COPY ca.crt /usr/local/share/ca-certificates/ca.crt

COPY --from=gcr.io/kaniko-project/executor:v1.22.0-debug /kaniko/ /kaniko/

RUN update-ca-certificates
RUN ls -l /etc/ssl/certs/ca-certificates.crt && \
    grep "My CA" /etc/ssl/certs/ca-certificates.crt || true

ENTRYPOINT ["/kaniko/executor"]