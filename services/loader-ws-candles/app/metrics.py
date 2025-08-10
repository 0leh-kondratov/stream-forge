from prometheus_client import Counter, Gauge, generate_latest
from fastapi import APIRouter, Response

metrics_router = APIRouter()

# Define Prometheus metrics
events_total = Counter(
    "loader_ws_candles_events_total",
    "Total number of events processed by loader-ws-candles",
    ["event_type"],
)

status_last = Gauge(
    "loader_ws_candles_status_last",
    "Last reported status of loader-ws-candles",
    ["status_type"],
)

errors_total = Counter(
    "loader_ws_candles_errors_total",
    "Total number of errors encountered by loader-ws-candles",
)

# Loader specific metrics
records_fetched_total = Counter(
    "loader_ws_candles_records_fetched_total",
    "Total number of records fetched from WebSocket",
)

records_published_total = Counter(
    "loader_ws_candles_records_published_total",
    "Total number of records published to Kafka",
)

@metrics_router.get("/metrics")
async def get_metrics():
    return Response(content=generate_latest().decode("utf-8"), media_type="text/plain")
