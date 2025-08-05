from pydantic import BaseModel, Field
from typing import Optional


class QueueTelemetry(BaseModel):
    queue_id: str = Field(
        ..., example="loader-btcusdt-api_candles_5m-2024_06_01-abc123",
        description="Уникальный идентификатор очереди"
    )
    telemetry_id: str = Field(
        ..., example="loader-producer__abc123",
        description="ID источника телеметрии (обычно соответствует pod или consumer)"
    )
    status: str = Field(
        ..., example="loading",
        description="Текущее состояние: started, loading, finished, error, interrupted"
    )
    message: Optional[str] = Field(
        default=None,
        example="Загрузка завершена успешно",
        description="Произвольное описание события"
    )
    records_written: Optional[int] = Field(
        default=None,
        example=123456,
        description="Количество обработанных/записанных записей"
    )
    finished: Optional[bool] = Field(
        default=False,
        example=True,
        description="Является ли событие финальным для очереди"
    )
    symbol: Optional[str] = Field(
        default=None,
        example="BTCUSDT",
        description="Торговая пара (символ), если передаётся"
    )
    type: Optional[str] = Field(
        default=None,
        example="api_candles_5m",
        description="Тип данных (например: ws_trades, api_orderbook)"
    )
    timestamp: float = Field(
        ..., example=1722346543.337,
        description="Временная метка телеметрии (unix timestamp)"
    )
    target: Optional[str] = Field(
        default=None,
        example="loader-producer",
        description="Целевой микросервис (опционально, может совпадать с telemetry_id)"
    )

    class Config:
        schema_extra = {
            "example": {
                "queue_id": "loader-btcusdt-api_candles_5m-2024_06_01-abc123",
                "telemetry_id": "loader-producer__abc123",
                "status": "loading",
                "message": "Загрузка в процессе",
                "records_written": 2048,
                "finished": False,
                "symbol": "BTCUSDT",
                "type": "api_candles_5m",
                "timestamp": 1722346543.337,
                "target": "loader-producer"
            }
        }
        extra = "forbid"
