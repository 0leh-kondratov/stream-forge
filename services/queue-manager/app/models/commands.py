from pydantic import BaseModel, Field
from typing import Literal, Optional, List


class QueueCommand(BaseModel):
    command: Literal["start", "stop"] = Field(
        ..., example="start", description="Тип команды: 'start' или 'stop'"
    )
    queue_id: str = Field(
        ..., example="loader-btcusdt-api_candles_5m-2024_06_01-abc123",
        description="Уникальный идентификатор очереди"
    )
    target: str = Field(
        ..., example="loader-producer",
        description="Название микросервиса-исполнителя"
    )
    timestamp: float = Field(
        ..., example=1722346211.177,
        description="Метка времени команды (unix timestamp)"
    )
    symbol: str = Field(
        ..., example="BTCUSDT",
        description="Название торгового инструмента"
    )
    type: str = Field(
        ..., example="api_candles_5m",
        description="Тип данных, например: api_candles_5m, ws_trades"
    )
    kafka_topic: str = Field(
        ..., example="loader-btcusdt-api-candles-5m-2024-06-01-abc123",
        description="Kafka topic, в который будут писаться данные"
    )
    telemetry_id: str = Field(
        ..., example="loader-producer__abc123",
        description="Идентификатор источника телеметрии"
    )
    image: str = Field(
        ..., example="registry.dmz.home/streamforge/loader-producer:v0.1.7",
        description="Docker-образ микросервиса"
    )
    time_range: Optional[str] = Field(
        default=None, example="2024-06-01:2024-06-02",
        description="Диапазон дат (для исторических данных)"
    )
    interval: Optional[str] = Field(
        default=None, example="5m",
        description="Интервал свечей или агрегации"
    )
    collection_name: Optional[str] = Field(
        default=None, example="btc_candles_5m_2024_06_01",
        description="Название коллекции в ArangoDB"
    )

    class Config:
        schema_extra = {
            "example": {
                "command": "start",
                "queue_id": "loader-btcusdt-api_candles_5m-2024_06_01-abc123",
                "target": "loader-producer",
                "timestamp": 1722346211.177,
                "symbol": "BTCUSDT",
                "type": "api_candles_5m",
                "kafka_topic": "loader-btcusdt-api-candles-5m-2024-06-01-abc123",
                "telemetry_id": "loader-producer__abc123",
                "image": "registry.dmz.home/streamforge/loader-producer:v0.1.7",
                "time_range": "2024-06-01:2024-06-02",
                "interval": "5m",
                "collection_name": "btc_candles_5m_2024_06_01"
            }
        }
        extra = "forbid"


class ServiceConfig(BaseModel):
    name: str = Field(..., description="Название микросервиса (например, loader-producer)")
    image: Optional[str] = Field(None, description="Docker-образ микросервиса")
    type: Optional[str] = Field(None, description="Тип данных, который обрабатывает сервис")
    kafka_topic: Optional[str] = Field(None, description="Kafka topic для сервиса")
    collection_name: Optional[str] = Field(None, description="Название коллекции в ArangoDB для сервиса")
    # Add other service-specific parameters as needed
    # For example, for loader-api-candles, you might have 'interval'
    interval: Optional[str] = Field(None, description="Интервал свечей или агрегации (для loader-api-candles)")


class StartQueueCommand(BaseModel):
    symbol: str = Field(..., example="BTCUSDT", description="Название торгового инструмента")
    time_range: str = Field(..., example="2024-06-01:2024-06-02", description="Диапазон дат (для исторических данных)")
    services: List[ServiceConfig] = Field(..., description="Список конфигураций микросервисов для запуска")

    class Config:
        schema_extra = {
            "example": {
                "symbol": "BTCUSDT",
                "time_range": "2024-07-01:2024-07-02",
                "services": [
                    {
                        "name": "loader-producer",
                        "image": "registry.dmz.home/streamforge/loader-producer:v0.1.7",
                        "type": "api_candles_5m",
                        "kafka_topic": "loader-btcusdt-api-candles-5m-2024-06-01-abc123"
                    },
                    {
                        "name": "arango-connector",
                        "image": "registry.dmz.home/streamforge/arango-connector:v0.1.0",
                        "type": "api_candles_5m",
                        "kafka_topic": "loader-btcusdt-api-candles-5m-2024-06-01-abc123",
                        "collection_name": "btc_candles_5m_2024_06_01"
                    }
                ]
            }
        }
        extra = "forbid"


class StartTestFlowCommand(BaseModel):
    symbol: str = Field(
        default="DUMMYUSDT",
        description="Символ для тестового прогона. Будет приведен к верхнему регистру."
    )
    time_range: str = Field(
        default="2024-01-01:2024-01-02",
        description="Небольшой диапазон дат для теста. Формат: YYYY-MM-DD:YYYY-MM-DD"
    )
    flow_name: str = Field(
        default="default_trade_flow",
        description="Название тестового прогона из файла test_flows.yaml"
    )

    class Config:
        schema_extra = {
            "example": {
                "symbol": "BTCUSDT",
                "time_range": "2024-07-01:2024-07-02",
                "flow_name": "default_trade_flow"
            }
        }