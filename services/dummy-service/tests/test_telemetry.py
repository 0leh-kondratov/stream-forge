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
    # Environment variables are now expected to be set externally
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
    mock_events = MagicMock()
    mock_status = MagicMock()
    mock_errors = MagicMock() # Added for consistency

    with patch('app.telemetry.dummy_events_total', mock_events), \
         patch('app.telemetry.dummy_status_last', mock_status), \
         patch('app.telemetry.dummy_errors_total', mock_errors): # Patch dummy_errors_total
        
        mock_events.labels.return_value.inc = MagicMock()
        mock_status.labels.return_value.set = MagicMock()
        mock_errors.inc = MagicMock() # Mock inc for dummy_errors_total

        metrics_mock_container = MagicMock()
        metrics_mock_container.dummy_events_total = mock_events
        metrics_mock_container.dummy_status_last = mock_status
        metrics_mock_container.dummy_errors_total = mock_errors # Add to container

        yield metrics_mock_container

@pytest.fixture(autouse=True)
def mock_logger():
    with patch('loguru.logger.debug') as mock_debug, \
         patch('loguru.logger.info') as mock_info, \
         patch('loguru.logger.error') as mock_error:
        yield MagicMock(debug=mock_debug, info=mock_info, error=mock_error)

@pytest.fixture
def telemetry_producer_instance():
    with patch('app.telemetry.AIOKafkaProducer') as MockAIOKafkaProducer:
        mock_producer_instance = MockAIOKafkaProducer.return_value
        mock_producer_instance.start = AsyncMock()
        mock_producer_instance.stop = AsyncMock()
        mock_producer_instance.send_and_wait = AsyncMock()
        
        instance = TelemetryProducer()
        instance.mock_producer_class = MockAIOKafkaProducer
        instance.mock_producer_instance = mock_producer_instance
        yield instance

# Test TelemetryProducer.__init__
def test_telemetry_producer_init(telemetry_producer_instance):
    assert telemetry_producer_instance.topic == os.getenv("QUEUE_EVENTS_TOPIC")
    assert telemetry_producer_instance.bootstrap_servers == os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    assert telemetry_producer_instance.username == os.getenv("KAFKA_USER")
    assert telemetry_producer_instance.password == os.getenv("KAFKA_PASSWORD")
    assert telemetry_producer_instance.ca_path == os.getenv("KAFKA_CA_PATH")
    assert telemetry_producer_instance.producer is None

# Test TelemetryProducer.start method
@pytest.mark.asyncio
async def test_telemetry_producer_start(telemetry_producer_instance, mock_ssl_context, mock_logger):
    await telemetry_producer_instance.start()

    mock_ssl_context.assert_called_once_with(ssl.PROTOCOL_TLS_CLIENT)
    mock_ssl_context.return_value.verify_mode = ssl.CERT_REQUIRED
    mock_ssl_context.return_value.load_verify_locations.assert_called_once_with(cafile=os.getenv("KAFKA_CA_PATH"))

    telemetry_producer_instance.mock_producer_class.assert_called_once_with(
        bootstrap_servers=telemetry_producer_instance.bootstrap_servers,
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-512",
        sasl_plain_username=telemetry_producer_instance.username,
        sasl_plain_password=telemetry_producer_instance.password,
        ssl_context=mock_ssl_context.return_value,
    )
    telemetry_producer_instance.mock_producer_instance.start.assert_called_once()
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
        "queue_id": os.getenv("QUEUE_ID"),
        "symbol": os.getenv("SYMBOL"),
        "type": os.getenv("TYPE", "dummy"),
        "producer": os.getenv("TELEMETRY_PRODUCER_ID", "dummy"),
        "sent_at": 12345.67,
    }
    if extra_data:
        expected_payload.update(extra_data)
    mock_metrics.dummy_events_total.labels.assert_called_once_with(event_type)
    mock_metrics.dummy_events_total.labels.return_value.inc.assert_called_once()
    mock_metrics.dummy_status_last.labels.assert_not_called() # Not a status event

    mock_aiokafka_producer.send_and_wait.assert_called_once_with(
        os.getenv("QUEUE_EVENTS_TOPIC"),
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
            "time_range": os.getenv("TIME_RANGE"),
            "kafka": os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
            "kafka_user": os.getenv("KAFKA_USER"),
            "kafka_topic": os.getenv("KAFKA_TOPIC"),
            "k8s_namespace": os.getenv("K8S_NAMESPACE"),
            "arango_url": os.getenv("ARANGO_URL"),
            "arango_db": os.getenv("ARANGO_DB"),
            "loader_image": os.getenv("LOADER_IMAGE"),
            "consumer_image": os.getenv("CONSUMER_IMAGE"),
        }
        if error_message:
            expected_payload["error_message"] = error_message
        if extra_data:
            expected_payload.update(extra_data)
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
async def test_simulate_failure(telemetry_producer_instance):
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
        mock_sys_exit.assert_called_once_with(1)