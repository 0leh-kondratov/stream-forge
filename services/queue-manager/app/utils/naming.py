"""
Утилиты для генерации стандартизированных имен и идентификаторов.
"""
import re
import shortuuid
from datetime import datetime

def sanitize_name(name: str) -> str:
    """Очищает строку для использования в именах ресурсов Kubernetes."""
    name = name.lower()
    name = re.sub(r'[^a-z0-9-]', '-', name)
    name = re.sub(r'^-+|-+$', '', name)
    return name

def get_date_part(time_range: str, separator: str = "_") -> str:
    """Извлекает дату начала из диапазона и форматирует ее."""
    if ":" not in time_range:
        return datetime.now().strftime(f"%Y{separator}%m{separator}%d")
    return time_range.split(":")[0].replace("-", separator)

def generate_ids(symbol: str, type_: str, time_range: str | None) -> dict:
    """
    Генерирует все необходимые идентификаторы для новой очереди на основе входных данных.
    """
    short_id = shortuuid.uuid()[:6]
    symbol_lower = symbol.lower()
    type_sanitized = sanitize_name(type_)
    
    if not time_range:
        time_range = datetime.now().strftime("%Y-%m-%d")

    date_part_id = get_date_part(time_range, "-")
    date_part_collection = get_date_part(time_range, "_")

    queue_id = f"loader-{symbol_lower}-{type_sanitized}-{date_part_id}-{short_id}"
    kafka_topic = queue_id

    # Генерация имени коллекции
    # btc_candles_5m_2024_06_01
    collection_parts = [symbol_lower]
    type_parts = type_.split('_')
    
    if len(type_parts) > 1:
        collection_parts.append(type_parts[1]) # candles, trades, etc.
    if "candles" in type_ and len(type_parts) > 2:
        collection_parts.append(type_parts[2]) # 1m, 5m, etc.
    
    collection_parts.append(date_part_collection)
    collection_name = "_".join(collection_parts)

    return {
        "queue_id": queue_id,
        "short_id": short_id,
        "kafka_topic": kafka_topic,
        "collection_name": collection_name,
    }