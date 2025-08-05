import os
from dotenv import load_dotenv
from pathlib import Path

# Загрузка переменных из .env
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# Основные параметры очереди
QUEUE_ID: str = os.getenv("QUEUE_ID")
SYMBOL: str = os.getenv("SYMBOL")
TIME_RANGE: str = os.getenv("TIME_RANGE", "2024-01-01:2024-01-02")
TYPE: str = os.getenv("TYPE", "api_candles_1m")
INTERVAL: str = os.getenv("INTERVAL", "1m")  # Например: 1m, 5m, 15m

# URL Binance API/WS
BINANCE_API_URL: str = os.getenv("BINANCE_API_URL", "https://api.binance.com")
BINANCE_WS_URL: str = os.getenv("BINANCE_WS_URL", "wss://stream.binance.com:9443/ws")

# Kafka
KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC")
KAFKA_USER: str = os.getenv("KAFKA_USER")
KAFKA_PASSWORD: str = os.getenv("KAFKA_PASSWORD")
CA_PATH: str = os.getenv("CA_PATH", "/usr/local/share/ca-certificates/ca.crt")

# Метки телеметрии и Webhook
WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
TELEMETRY_TOPIC: str = os.getenv("TELEMETRY_TOPIC", "queue-events")
CONTROL_TOPIC: str = os.getenv("CONTROL_TOPIC", "queue-control")

# Интервал отправки телеметрии (в секундах)
TELEMETRY_INTERVAL: int = int(os.getenv("TELEMETRY_INTERVAL", 5))

# Режим отладки
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
