import os
from pydantic import BaseSettings, Field
from functools import lru_cache


class Settings(BaseSettings):
    # === General Parameters ===
    DEBUG: bool = Field(default=False)
    K8S_NAMESPACE: str = Field(default="stf")

    # === Kafka ===
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_USER: str
    KAFKA_PASSWORD: str
    CA_PATH: str = "/usr/local/share/ca-certificates/ca.crt"

    # === Kafka Topics ===
    QUEUE_CONTROL_TOPIC: str = Field(default="queue-control")
    QUEUE_EVENTS_TOPIC: str = Field(default="queue-events")

    # === ArangoDB ===
    ARANGO_URL: str
    ARANGO_DB: str
    ARANGO_USER: str
    ARANGO_PASSWORD: str

    # === Microservice Images ===
    LOADER_IMAGE: str
    CONSUMER_IMAGE: str
    GNN_TRAINER_IMAGE: str
    VISUALIZER_IMAGE: str
    GRAPH_BUILDER_IMAGE: str = Field(default="registry.dmz.home/streamforge/graph-builder:v0.1.0")

    # === MinIO (optional) ===
    MINIO_ENDPOINT: str = Field(default="")
    MINIO_ACCESS_KEY: str = Field(default="")
    MINIO_SECRET_KEY: str = Field(default="")
    MINIO_BUCKET: str = Field(default="streamforge")
    MINIO_SECURE: bool = Field(default=True)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings():
    return Settings()


# Global settings
settings = get_settings()
