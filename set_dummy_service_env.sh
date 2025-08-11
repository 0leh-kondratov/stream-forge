#!/bin/bash

# This script sets essential environment variables for the dummy-service.
# Remember to replace placeholder values with actual credentials and configurations.

export QUEUE_EVENTS_TOPIC="queue-events"
export KAFKA_BOOTSTRAP_SERVERS="k3-kafka-bootstrap.kafka:9093"
export KAFKA_USER="user-streamforge"
export KAFKA_PASSWORD="qqIJ511mX1c2FOpNZDGaw5WqblS1pxeD"
export KAFKA_CA_PATH="/data/projects/stream-forge/services/dummy-service/ca.crt" # This should be the path inside the container/environment
export QUEUE_ID="BTCUSDT"
export SYMBOL="BTCUSDT"
export TYPE="dummy"
export TELEMETRY_PRODUCER_ID="your-telemetry-producer-id"
export TIME_RANGE="2024-01-01:2024-01-02"
export KAFKA_TOPIC="BTCUSDT-rest"
export K8S_NAMESPACE="stf"
export ARANGO_URL="http://abase-3.dmz.home:8529"
export ARANGO_DB="streamforge"
export LOADER_IMAGE="registry.dmz.home/streamforge/loader-producer:v0.1.7"
export CONSUMER_IMAGE="registry.dmz.home/streamforge/arango-connector:v0.1.0"
export QUEUE_CONTROL_TOPIC="queue-control"
export BINANCE_API_KEY="eCqyyuQauR9XqctgI3OtKuI7AFqJOKNalw0qBRR28hVnwa93C6VMdr7vW8ynwu1d"
export BINANCE_API_SECRET="SvBquPaIwzMlUCMsI6QcPUvmJENbxEyvUZO9iabn6JGCeEtdAYesWeHRyN3G90jv"
export TELEGRAM_BOT_TOKEN="7915103866:AAFbTvZb9NpoME0M0VsqrYzUXa9SIqjL17g"
export TELEGRAM_CHAT_ID="414744220"

echo "Environment variables set for dummy-service."
echo "Remember to replace placeholder values with actual credentials and configurations."
