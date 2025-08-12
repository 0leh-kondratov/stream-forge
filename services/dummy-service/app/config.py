# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_USER = os.getenv("KAFKA_USER")
KAFKA_PASSWORD = os.getenv("KAFKA_PASSWORD")
CA_PATH = os.getenv("CA_PATH")

QUEUE_CONTROL_TOPIC = os.getenv("QUEUE_CONTROL_TOPIC")
QUEUE_EVENTS_TOPIC = os.getenv("QUEUE_EVENTS_TOPIC")

QUEUE_ID = os.getenv("QUEUE_ID", "unknown-queue")
SYMBOL = os.getenv("SYMBOL", "BTCUSDT")
TYPE = os.getenv("TYPE", "api_candles_5m")
INTERVAL = os.getenv("INTERVAL", "5m")
TIME_RANGE = os.getenv("TIME_RANGE")

TELEMETRY_PRODUCER_ID = os.getenv("TELEMETRY_PRODUCER_ID", "dummy-telemetry")
