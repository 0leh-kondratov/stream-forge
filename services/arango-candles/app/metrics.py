from prometheus_client import Counter, Gauge, generate_latest
from fastapi import APIRouter, Response

metrics_router = APIRouter()

# Define Prometheus metrics
events_total = Counter(
    "arango_candles_events_total",
    "Total number of events processed by arango-candles",
    ["event_type"],
)

status_last = Gauge(
    "arango_candles_status_last",
    "Last reported status of arango-candles",
    ["status_type"],
)

errors_total = Counter(
    "arango_candles_errors_total",
    "Total number of errors encountered by arango-candles",
)

@metrics_router.get("/metrics")
async def get_metrics():
    return Response(content=generate_latest().decode("utf-8"), media_type="text/plain")
