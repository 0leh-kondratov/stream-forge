import pytest
from unittest.mock import MagicMock, patch
from fastapi import Response
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from app.metrics import (
    dummy_events_total,
    dummy_pings_total,
    dummy_pongs_total,
    dummy_errors_total,
    dummy_status_last,
    metrics_router,
    metrics
)

# Test metric initialization
def test_dummy_events_total_initialization():
    assert isinstance(dummy_events_total, Counter)
    assert dummy_events_total._name == "dummy_events"
    assert dummy_events_total._documentation == "Total telemetry events sent"
    assert dummy_events_total._labelnames == ("event",)

def test_dummy_pings_total_initialization():
    assert isinstance(dummy_pings_total, Counter)
    assert dummy_pings_total._name == "dummy_pings"
    assert dummy_pings_total._documentation == "Ping commands received"
    assert dummy_pings_total._labelnames == ()

def test_dummy_pongs_total_initialization():
    assert isinstance(dummy_pongs_total, Counter)
    assert dummy_pongs_total._name == "dummy_pongs"
    assert dummy_pongs_total._documentation == "Pong responses sent"
    assert dummy_pongs_total._labelnames == ()

def test_dummy_errors_total_initialization():
    assert isinstance(dummy_errors_total, Counter)
    assert dummy_errors_total._name == "dummy_errors"
    assert dummy_errors_total._documentation == "Fatal errors occurred"
    assert dummy_errors_total._labelnames == ()

def test_dummy_status_last_initialization():
    assert isinstance(dummy_status_last, Gauge)
    assert dummy_status_last._name == "dummy_status_last"
    assert dummy_status_last._documentation == "Last known status"
    assert dummy_status_last._labelnames == ("status",)

# Test /metrics endpoint
def test_metrics_endpoint():
    mock_generate_latest_output = b"# HELP dummy_pings_total Ping commands received\n# TYPE dummy_pings_total counter\ndummy_pings_total 0.0\n"
    with patch('app.metrics.generate_latest', return_value=mock_generate_latest_output) as mock_generate_latest_func: # Capture the mock
        response = metrics()

        assert isinstance(response, Response)
        assert response.media_type == CONTENT_TYPE_LATEST
        assert response.body == mock_generate_latest_output

        # Verify that generate_latest was called
        mock_generate_latest_func.assert_called_once()
