from prometheus_client import Counter, Gauge, generate_latest
from fastapi import APIRouter, Response

metrics_router = APIRouter()

# Define Prometheus metrics
events_total = Counter(
    "arango_connector_events_total",
    "Total number of events processed by arango-connector",
    ["event_type"],
)

status_last = Gauge(
    "arango_connector_status_last",
    "Last reported status of arango-connector",
    ["status_type"],
)

errors_total = Counter(
    "arango_connector_errors_total",
    "Total number of errors encountered by arango-connector",
)

@metrics_router.get("/metrics")
async def get_metrics():
    return Response(content=generate_latest().decode("utf-8"), media_type="text/plain")
