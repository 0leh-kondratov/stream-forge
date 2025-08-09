import pytest
import os
import json
import time
import ssl
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.telemetry import TelemetryProducer, log_startup_event, simulate_loading, simulate_failure
from app.metrics import dummy_events_total, dummy_status_last

# Mock environment variables
@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict(os.environ, {
        "QUEUE_EVENTS_TOPIC": "test-events",
        "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
        "KAFKA_USER": "testuser",
        "KAFKA_PASSWORD": "testpassword",
        "KAFKA_CA_PATH": "/etc/ssl/certs/ca.crt",
        "QUEUE_ID": "test_queue_id",
        "SYMBOL": "TEST",
        "TYPE": "dummy",
        "TELEMETRY_PRODUCER_ID": "dummy_producer",
        "TIME_RANGE": "1h",
        "KAFKA_TOPIC": "test-kafka-topic",
        "K8S_NAMESPACE": "test-namespace",
        "ARANGO_URL": "http://localhost:8529",
        "ARANGO_DB": "test_db",
        "LOADER_IMAGE": "loader:latest",
        "CONSUMER_IMAGE": "consumer:latest",
    }):
        yield

# Mock external dependencies
@pytest.fixture
def mock_aiokafka_producer():
    mock = AsyncMock()
    mock.start = AsyncMock()
    mock.stop = AsyncMock()
    mock.send_and_wait = AsyncMock()
    return mock

@pytest.fixture
def mock_ssl_context():
    with patch('ssl.SSLContext') as mock:
        yield mock

@pytest.fixture(autouse=True)
def mock_metrics():
    with patch('app.metrics.dummy_events_total', MagicMock()) as mock_events, \
         patch('app.metrics.dummy_status_last', MagicMock()) as mock_status:
        mock_events.labels.return_value.inc = MagicMock()
        mock_status.labels.return_value.set = MagicMock()
        yield

@pytest.fixture(autouse=True)
def mock_logger():
    with patch('loguru.logger.debug') as mock_debug, \
         patch('loguru.logger.info') as mock_info, \
         patch('loguru.logger.error') as mock_error:
        yield MagicMock(debug=mock_debug, info=mock_info, error=mock_error)

@pytest.fixture
def telemetry_producer_instance(mock_aiokafka_producer):
    with patch('aiokafka.AIOKafkaProducer', return_value=mock_aiokafka_producer):
        return TelemetryProducer()

# Test TelemetryProducer.__init__
def test_telemetry_producer_init(telemetry_producer_instance):
    assert telemetry_producer_instance.topic == "test-events"
    assert telemetry_producer_instance.bootstrap_servers == "localhost:9092"
    assert telemetry_producer_instance.username == "testuser"
    assert telemetry_producer_instance.password == "testpassword"
    assert telemetry_producer_instance.ca_path == "/etc/ssl/certs/ca.crt"
    assert telemetry_producer_instance.producer is None

# Test TelemetryProducer.start method
@pytest.mark.asyncio
async def test_telemetry_producer_start(telemetry_producer_instance, mock_aiokafka_producer, mock_ssl_context, mock_logger):
    await telemetry_producer_instance.start()

    mock_ssl_context.assert_called_once_with(ssl.PROTOCOL_TLS_CLIENT)
    mock_ssl_context.return_value.verify_mode = ssl.CERT_REQUIRED
    mock_ssl_context.return_value.load_verify_locations.assert_called_once_with(cafile="/etc/ssl/certs/ca.crt")

    mock_aiokafka_producer.start.assert_called_once()
    mock_logger.debug.assert_called_once_with("Telemetry producer started.")

# Test TelemetryProducer.stop method
@pytest.mark.asyncio
async def test_telemetry_producer_stop(telemetry_producer_instance, mock_aiokafka_producer):
    telemetry_producer_instance.producer = mock_aiokafka_producer
    await telemetry_producer_instance.stop()
    mock_aiokafka_producer.stop.assert_called_once()

@pytest.mark.asyncio
async def test_telemetry_producer_stop_no_producer(telemetry_producer_instance):
    telemetry_producer_instance.producer = None
    await telemetry_producer_instance.stop() # Should not raise error

# Test TelemetryProducer.send_event method
@pytest.mark.asyncio
async def test_telemetry_producer_send_event(telemetry_producer_instance, mock_aiokafka_producer, mock_metrics, mock_logger):
    telemetry_producer_instance.producer = mock_aiokafka_producer
    event_type = "test_event"
    extra_data = {"key": "value"}

    with patch('time.time', return_value=12345.67):
        await telemetry_producer_instance.send_event(event_type, extra_data)

    expected_payload = {
        "event": event_type,
        "queue_id": "test_queue_id",
        "symbol": "TEST",
        "type": "dummy",
        "producer": "dummy_producer",
        "sent_at": 12345.67,
        "key": "value"
    }
    mock_metrics.dummy_events_total.labels.assert_called_once_with(event_type)
    mock_metrics.dummy_events_total.labels.return_value.inc.assert_called_once()
    mock_metrics.dummy_status_last.labels.assert_not_called() # Not a status event

    mock_aiokafka_producer.send_and_wait.assert_called_once_with(
        "test-events",
        json.dumps(expected_payload).encode()
    )
    mock_logger.info.assert_called_once_with(f"Event sent: {event_type}")

@pytest.mark.asyncio
async def test_telemetry_producer_send_event_with_status_type(telemetry_producer_instance, mock_aiokafka_producer, mock_metrics):
    telemetry_producer_instance.producer = mock_aiokafka_producer
    event_type = "started"

    with patch('time.time', return_value=12345.67):
        await telemetry_producer_instance.send_event(event_type)

    mock_metrics.dummy_status_last.labels.assert_called_once_with(event_type)
    mock_metrics.dummy_status_last.labels.return_value.set.assert_called_once_with(1)

# Test TelemetryProducer.send_status_update method
@pytest.mark.asyncio
async def test_telemetry_producer_send_status_update(telemetry_producer_instance, mock_logger):
    telemetry_producer_instance.producer = AsyncMock() # Ensure producer is mocked
    status = "finished"
    message = "Test message"
    finished = True
    records_written = 100
    error_message = "Test error"
    extra_data = {"custom": "data"}

    with patch.object(telemetry_producer_instance, 'send_event', new=AsyncMock()) as mock_send_event:
        await telemetry_producer_instance.send_status_update(
            status=status,
            message=message,
            finished=finished,
            records_written=records_written,
            error_message=error_message,
            extra=extra_data
        )

        expected_payload = {
            "status": status,
            "message": message,
            "finished": finished,
            "records_written": records_written,
            "time_range": "1h",
            "kafka": "localhost:9092",
            "kafka_user": "testuser",
            "kafka_topic": "test-kafka-topic",
            "k8s_namespace": "test-namespace",
            "arango_url": "http://localhost:8529",
            "arango_db": "test_db",
            "loader_image": "loader:latest",
            "consumer_image": "consumer:latest",
            "error_message": error_message,
            "custom": "data"
        }
        mock_send_event.assert_called_once_with(status, expected_payload)
        mock_logger.info.assert_called_once()
        assert "Telemetry status update" in mock_logger.info.call_args[0][0]

# Test log_startup_event function
@pytest.mark.asyncio
async def test_log_startup_event(telemetry_producer_instance):
    with patch.object(telemetry_producer_instance, 'send_status_update', new=AsyncMock()) as mock_send_status_update:
        await log_startup_event(telemetry_producer_instance)
        mock_send_status_update.assert_called_once_with(
            status="started",
            message="Микросервис запущен",
            finished=False,
            records_written=0,
        )

# Test simulate_loading function
@pytest.mark.asyncio
async def test_simulate_loading(telemetry_producer_instance):
    with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep, \
         patch.object(telemetry_producer_instance, 'send_status_update', new=AsyncMock()) as mock_send_status_update:
        
        # Run for a few iterations
        mock_sleep.side_effect = [None, None, asyncio.CancelledError] # Stop after 2 iterations

        try:
            await simulate_loading(telemetry_producer_instance)
        except asyncio.CancelledError:
            pass

        assert mock_sleep.call_count == 3
        assert mock_send_status_update.call_count == 2
        mock_send_status_update.assert_any_call(
            status="loading",
            message="Загрузка продолжается, batch 1",
            records_written=100
        )
        mock_send_status_update.assert_any_call(
            status="loading",
            message="Загрузка продолжается, batch 2",
            records_written=200
        )

# Test simulate_failure function
@pytest.mark.asyncio
async def test_simulate_failure(telemetry_producer_instance, mock_logger):
    delay_sec = 1
    with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep, \
         patch('sys.exit') as mock_sys_exit, \
         patch.object(telemetry_producer_instance, 'send_status_update', new=AsyncMock()) as mock_send_status_update:
        
        await simulate_failure(delay_sec, telemetry_producer_instance)

        mock_sleep.assert_called_once_with(delay_sec)
        mock_send_status_update.assert_called_once_with(
            status="error",
            message="Ошибка тестовая: симулирован сбой",
            finished=True,
            error_message="Simulated failure triggered by --fail-after"
        )
        mock_logger.error.assert_called_once_with("Simulated failure — exiting")
        mock_sys_exit.assert_called_once_with(1)
