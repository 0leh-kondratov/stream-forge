import os
from dotenv import load_dotenv
from pathlib import Path

# Загрузка переменных из .env
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# Основные параметры очереди
QUEUE_ID: str = os.getenv("QUEUE_ID")
SYMBOL: str = os.getenv("SYMBOL")
TYPE: str = os.getenv("TYPE")
KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC") # Output Kafka topic for candle data
TIME_RANGE: str = os.getenv("TIME_RANGE") # e.g., "2023-01-01:2023-01-02"
INTERVAL: str = os.getenv("INTERVAL", "1h") # e.g., "1m", "1h", "1d"

# Kafka
KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_USER: str = os.getenv("KAFKA_USER")
KAFKA_PASSWORD: str = os.getenv("KAFKA_PASSWORD")
KAFKA_CA_PATH: str = os.getenv("KAFKA_CA_PATH")
QUEUE_CONTROL_TOPIC: str = os.getenv("QUEUE_CONTROL_TOPIC", "queue-control")
QUEUE_EVENTS_TOPIC: str = os.getenv("QUEUE_EVENTS_TOPIC", "queue-events")

# External API (e.g., Binance)
BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET: str = os.getenv("BINANCE_API_SECRET")

# Телеметрия
TELEMETRY_PRODUCER_ID: str = os.getenv("TELEMETRY_PRODUCER_ID")

# Kubernetes and ArangoDB
K8S_NAMESPACE: str = os.getenv("K8S_NAMESPACE")
ARANGO_URL: str = os.getenv("ARANGO_URL")
ARANGO_DB: str = os.getenv("ARANGO_DB")

# Image versions
LOADER_IMAGE: str = os.getenv("LOADER_IMAGE")
CONSUMER_IMAGE: str = os.getenv("CONSUMER_IMAGE")
