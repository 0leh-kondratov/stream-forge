from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    ARANGO_URL: str = "http://localhost:8529"
    ARANGO_DB: str = "streamforge"
    ARANGO_USER: str = "root"
    ARANGO_PASSWORD: str = "root"

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_USER: str | None = None
    KAFKA_PASSWORD: str | None = None
    CA_PATH: Path | None = None

    QUEUE_CONTROL_TOPIC: str = "queue-control"
    QUEUE_EVENTS_TOPIC: str = "queue-events"
    KAFKA_TOPIC: str = "visualizer-topic"
    QUEUE_ID: str = "default-visualizer-queue-id"

    TELEMETRY_PRODUCER_ID: str = "visualizer"

    FRONTEND_PATH: Path = Path("/app/frontend")
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    TESTING: bool = False # New setting for testing mode

settings = Settings()
