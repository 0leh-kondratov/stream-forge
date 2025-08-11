from prometheus_client import Counter, Gauge, Histogram

# Define Prometheus metrics
records_fetched_total = Counter('records_fetched_total', 'Total number of records fetched from source API')
records_published_total = Counter('records_published_total', 'Total number of records published to Kafka')
errors_total = Counter('errors_total', 'Total number of errors encountered')

# Example of a Gauge for current status, if needed
# current_status = Gauge('current_status', 'Current status of the loader (0=idle, 1=loading, etc.)')

# Example of a Histogram for processing time, if needed
# processing_time_seconds = Histogram('processing_time_seconds', 'Time spent processing each record')

# FastAPI metrics router (placeholder, actual implementation might be in main.py or a separate file)
from fastapi import APIRouter

metrics_router = APIRouter()

@metrics_router.get("/metrics")
async def get_metrics():
    from prometheus_client import generate_latest
    return generate_latest()