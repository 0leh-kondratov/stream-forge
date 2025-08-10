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

# Kafka (if GNN trainer is triggered by Kafka)
KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC") # Input Kafka topic for graph data
KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_USER: str = os.getenv("KAFKA_USER_CONSUMER")
KAFKA_PASSWORD: str = os.getenv("KAFKA_PASSWORD_CONSUMER")
CA_PATH: str = os.getenv("CA_PATH")
QUEUE_CONTROL_TOPIC: str = os.getenv("QUEUE_CONTROL_TOPIC", "queue-control")
QUEUE_EVENTS_TOPIC: str = os.getenv("QUEUE_EVENTS_TOPIC", "queue-events")

# ArangoDB (for loading graph data)
ARANGO_URL: str = os.getenv("ARANGO_URL")
ARANGO_DB: str = os.getenv("ARANGO_DB")
ARANGO_USER: str = os.getenv("ARANGO_USER")
ARANGO_PASSWORD: str = os.getenv("ARANGO_PASSWORD")
GRAPH_COLLECTION_NAME: str = os.getenv("GRAPH_COLLECTION_NAME") # Collection where graph data is stored

# Minio (for storing trained models)
MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME")

# Telemetry
TELEMETRY_PRODUCER_ID: str = os.getenv("TELEMETRY_PRODUCER_ID")

# Training specific parameters
MODEL_NAME: str = os.getenv("MODEL_NAME", "gnn_model")
EPOCHS: int = int(os.getenv("EPOCHS", "100"))
LEARNING_RATE: float = float(os.getenv("LEARNING_RATE", "0.01"))
