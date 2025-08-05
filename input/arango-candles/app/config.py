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
KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC")
COLLECTION_NAME: str = os.getenv("COLLECTION_NAME")

# Kafka
KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
# Используем пользователя-консьюмера
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

# Телеметрия
TELEMETRY_PRODUCER_ID: str = os.getenv("TELEMETRY_PRODUCER_ID")