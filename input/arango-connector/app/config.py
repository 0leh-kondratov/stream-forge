import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# Kafka
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "k3-kafka-bootstrap.kafka:9093")
KAFKA_USER = os.getenv("KAFKA_USER", "user-streamforge")
KAFKA_PASSWORD = os.getenv("KAFKA_PASSWORD", "")
CA_PATH = os.getenv("CA_PATH", "/usr/local/share/ca-certificates/ca.crt")

QUEUE_ID = os.getenv("QUEUE_ID", "default-queue")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "btcusdt-api")
QUEUE_CONTROL_TOPIC = os.getenv("QUEUE_CONTROL_TOPIC", "queue-control")
QUEUE_EVENTS_TOPIC = os.getenv("QUEUE_EVENTS_TOPIC", "queue-events")

# ArangoDB
ARANGO_URL = os.getenv("ARANGO_URL", "http://abase-1.dmz.home:8529")
ARANGO_DB = os.getenv("ARANGO_DB", "streamforge")
ARANGO_USER = os.getenv("ARANGO_USER", "root")
ARANGO_PASSWORD = os.getenv("ARANGO_PASSWORD", "")

COLLECTION_NAME = os.getenv("COLLECTION_NAME", f"{KAFKA_TOPIC}-raw")

# Формат данных: candles / trades / other
DATA_TYPE = os.getenv("DATA_TYPE", "candles")

# Период агрегации для индикаторов (по умолчанию 14)
INDICATOR_PERIOD = int(os.getenv("INDICATOR_PERIOD", "14"))

# Интервал обновления телеметрии
TELEMETRY_INTERVAL = float(os.getenv("TELEMETRY_INTERVAL", "5.0"))

# ID продюсера телеметрии
TELEMETRY_PRODUCER_ID = os.getenv("TELEMETRY_PRODUCER_ID", "arango-connector")
