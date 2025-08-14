# app/metrics/prometheus_metrics.py

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time

# HTTP metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "http_status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["endpoint"]
)

# Queue metrics
QUEUE_COMMANDS_TOTAL = Counter(
    "queue_commands_total",
    "Total number of queue control commands sent",
    ["command", "target"]
)

TELEMETRY_EVENTS_TOTAL = Counter(
    "telemetry_events_total",
    "Total telemetry events received",
    ["status", "producer"]
)

def setup_metrics(app):
    """
    Middleware for collecting HTTP metrics.
    """
    @app.middleware("http")
    async def metrics_middleware(request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            http_status=response.status_code
        ).inc()

        return response

    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
