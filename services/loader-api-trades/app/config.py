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
KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC") # Output Kafka topic for trade data
TIME_RANGE: str = os.getenv("TIME_RANGE") # e.g., "2023-01-01:2023-01-02"
LIMIT: int = int(os.getenv("LIMIT", "1000")) # Max number of trades per request

# Kafka
KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_USER: str = os.getenv("KAFKA_USER_PRODUCER") # Use producer user
KAFKA_PASSWORD: str = os.getenv("KAFKA_PASSWORD_PRODUCER")
CA_PATH: str = os.getenv("CA_PATH")
QUEUE_CONTROL_TOPIC: str = os.getenv("QUEUE_CONTROL_TOPIC", "queue-control")
QUEUE_EVENTS_TOPIC: str = os.getenv("QUEUE_EVENTS_TOPIC", "queue-events")

# External API (e.g., Binance)
BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET: str = os.getenv("BINANCE_API_SECRET")

# Телеметрия
TELEMETRY_PRODUCER_ID: str = os.getenv("TELEMETRY_PRODUCER_ID")
