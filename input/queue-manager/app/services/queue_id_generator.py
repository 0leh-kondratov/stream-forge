import uuid
from datetime import datetime

def generate_queue_id(symbol: str, type_: str, time_range: str) -> str:
    """
    Формат: loader-btcusdt-api_candles_5m-2024_06_01-abc123
    """
    date_part = time_range.split(":")[0].replace("-", "_")
    short_id = uuid.uuid4().hex[:6]
    return f"loader-{symbol.lower()}-{type_.replace('.', '_')}-{date_part}-{short_id}"
