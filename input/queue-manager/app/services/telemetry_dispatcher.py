from datetime import datetime
from app.services.arango_service import ArangoQueueStore
from loguru import logger

store = ArangoQueueStore()
store.connect()

def save_telemetry_event(event: dict):
    try:
        event["_key"] = f"{event['queue_id']}::{event.get('producer', 'unknown')}::{int(event['timestamp'])}"
        event["received_at"] = datetime.utcnow().isoformat()
        store.insert_document("telemetry", event)
        logger.debug(f"🧭 Телеметрия сохранена в ArangoDB: {event['_key']}")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка записи телеметрии: {e}")
