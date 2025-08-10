from prometheus_client import Counter, Gauge, generate_latest
from fastapi import APIRouter, Response

metrics_router = APIRouter()

# Define Prometheus metrics
events_total = Counter(
    "arango_graph_prep_events_total",
    "Total number of events processed by arango-graph-prep",
    ["event_type"],
)

status_last = Gauge(
    "arango_graph_prep_status_last",
    "Last reported status of arango-graph-prep",
    ["status_type"],
)

errors_total = Counter(
    "arango_graph_prep_errors_total",
    "Total number of errors encountered by arango-graph-prep",
)

@metrics_router.get("/metrics")
async def get_metrics():
    return Response(content=generate_latest().decode("utf-8"), media_type="text/plain")
