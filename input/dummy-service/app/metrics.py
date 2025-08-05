# app/metrics.py
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response

metrics_router = APIRouter()

dummy_events_total = Counter("dummy_events_total", "Total telemetry events sent", ["event"])
dummy_pings_total = Counter("dummy_pings_total", "Ping commands received")
dummy_pongs_total = Counter("dummy_pongs_total", "Pong responses sent")
dummy_errors_total = Counter("dummy_errors_total", "Fatal errors occurred")
dummy_status_last = Gauge("dummy_status_last", "Last known status", ["status"])

@metrics_router.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
