import os
from dotenv import load_dotenv
from pathlib import Path

# Load variables from .env
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# Basic queue parameters
QUEUE_ID: str = os.getenv("QUEUE_ID")
SYMBOL: str = os.getenv("SYMBOL")
TYPE: str = os.getenv("TYPE")
KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC") # Input Kafka topic for trade data
COLLECTION_NAME: str = os.getenv("COLLECTION_NAME") # ArangoDB collection for trade data

# Kafka
KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
# Use consumer user
KAFKA_USER: str = os.getenv("KAFKA_USER_CONSUMER")
KAFKA_PASSWORD: str = os.getenv("KAFKA_PASSWORD_CONSUMER")
CA_PATH: str = os.getenv("CA_PATH")
QUEUE_CONTROL_TOPIC: str = os.getenv("QUEUE_CONTROL_TOPIC", "queue-control")
QUEUE_EVENTS_TOPIC: str = os.getenv("QUEUE_EVENTS_TOPIC", "queue-events")

# ArangoDB
ARANGO_URL: str = os.getenv("ARANGO_URL")
ARANGO_DB: str = os.getenv("ARANGO_DB")
ARANGO_USER: str = os.getenv("ARANGO_USER")
ARANGO_PASSWORD: str = os.getenv("ARANGO_PASSWORD")

# Telemetry
TELEMETRY_PRODUCER_ID: str = os.getenv("TELEMETRY_PRODUCER_ID")
