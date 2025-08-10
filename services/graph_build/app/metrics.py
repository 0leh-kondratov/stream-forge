from prometheus_client import Counter, Gauge, generate_latest
from fastapi import APIRouter, Response

metrics_router = APIRouter()

# Define Prometheus metrics
events_total = Counter(
    "graph_build_events_total",
    "Total number of events processed by graph-build",
    ["event_type"],
)

status_last = Gauge(
    "graph_build_status_last",
    "Last reported status of graph-build",
    ["status_type"],
)

errors_total = Counter(
    "graph_build_errors_total",
    "Total number of errors encountered by graph-build",
)

@metrics_router.get("/metrics")
async def get_metrics():
    return Response(content=generate_latest().decode("utf-8"), media_type="text/plain")
