from prometheus_client import Counter, Gauge, generate_latest
from fastapi import APIRouter, Response

metrics_router = APIRouter()

# Define Prometheus metrics
events_total = Counter(
    "gnn_trainer_events_total",
    "Total number of events processed by gnn-trainer",
    ["event_type"],
)

status_last = Gauge(
    "gnn_trainer_status_last",
    "Last reported status of gnn-trainer",
    ["status_type"],
)

errors_total = Counter(
    "gnn_trainer_errors_total",
    "Total number of errors encountered by gnn-trainer",
)

# GNN specific metrics
training_epochs_completed = Counter(
    "gnn_trainer_epochs_completed_total",
    "Total number of training epochs completed",
)

training_loss = Gauge(
    "gnn_trainer_current_training_loss",
    "Current training loss of the GNN model",
)

model_saved_total = Counter(
    "gnn_trainer_models_saved_total",
    "Total number of GNN models saved",
)

@metrics_router.get("/metrics")
async def get_metrics():
    return Response(content=generate_latest().decode("utf-8"), media_type="text/plain")
