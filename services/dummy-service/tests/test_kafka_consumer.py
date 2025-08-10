import pytest
import os
import json
import asyncio
import ssl
import time
from unittest.mock import AsyncMock, MagicMock, patch
from app.kafka_consumer import KafkaCommandConsumer, AIOKafkaConsumer
from app.metrics import dummy_pings_total, dummy_pongs_total

# Mock environment variables
@pytest.fixture(autouse=True)
def mock_env_vars(tmp_path):
    # Environment variables are now expected to be set externally
    yield

# Mock external dependencies
@pytest.fixture
def mock_telemetry_producer():
    mock = MagicMock()
    mock.send_event = AsyncMock()
    mock.send_status_update = AsyncMock()
    return mock

@pytest.fixture
def mock_aiokafka_consumer():
    mock = AsyncMock(spec=AIOKafkaConsumer)

    # Mock the async iterator behavior
    async def aiter_mock():
        yield MagicMock(value=b'{"command": "ping"}', key=b'some_key')
        # To stop the async for loop after one iteration in tests
        raise StopAsyncIteration

    mock.__aiter__.side_effect = aiter_mock
    mock.__anext__.side_effect = aiter_mock

    return mock

@pytest.fixture
def mock_ssl_context():
    with patch('ssl.SSLContext') as mock:
        yield mock

@pytest.fixture(autouse=True) # Consider removing autouse if not all tests need it
def mock_metrics():
    mock_pings = MagicMock()
    mock_pongs = MagicMock()
    mock_events = MagicMock() # Need to mock dummy_events_total as well
    mock_status = MagicMock() # Need to mock dummy_status_last as well
    mock_errors = MagicMock() # Need to mock dummy_errors_total as well

    with patch('app.metrics.dummy_pings_total', mock_pings), \
         patch('app.metrics.dummy_pongs_total', mock_pongs), \
         patch('app.metrics.dummy_events_total', mock_events), \
         patch('app.metrics.dummy_status_last', mock_status), \
         patch('app.metrics.dummy_errors_total', mock_errors):
        
        # Mock the .inc() and .labels() methods
        mock_pings.inc = MagicMock()
        mock_pongs.inc = MagicMock()
        mock_events.labels.return_value.inc = MagicMock() # For dummy_events_total.labels(event_type).inc()
        mock_status.labels.return_value.set = MagicMock() # For dummy_status_last.labels(event_type).set(1)
        mock_errors.inc = MagicMock() # For dummy_errors_total.inc()

        # Create a container mock to return to the test function
        metrics_mock_container = MagicMock()
        metrics_mock_container.dummy_pings_total = mock_pings
        metrics_mock_container.dummy_pongs_total = mock_pongs
        metrics_mock_container.dummy_events_total = mock_events
        metrics_mock_container.dummy_status_last = mock_status
        metrics_mock_container.dummy_errors_total = mock_errors

        yield metrics_mock_container # Yield the container mock


@pytest.fixture
def mock_asyncio_event():
    mock = AsyncMock(spec=asyncio.Event)
    mock.set = MagicMock()
    return mock

@pytest.fixture
def consumer_instance(mock_telemetry_producer, mock_asyncio_event, mock_aiokafka_consumer):
    with patch('app.kafka_consumer.AIOKafkaConsumer') as MockAIOKafkaConsumer:
        MockAIOKafkaConsumer.return_value = mock_aiokafka_consumer
        instance = KafkaCommandConsumer(
            queue_id=os.getenv("QUEUE_ID"),
            telemetry_producer=mock_telemetry_producer,
            exit_on_ping=False,
            shutdown_event=mock_asyncio_event
        )
        # Attach the mock to the instance for access in tests
        instance.mock_consumer_class = MockAIOKafkaConsumer
        instance.mock_consumer_instance = mock_aiokafka_consumer # Use the pre-configured mock
        yield instance

# Test __init__
def test_consumer_init(consumer_instance, mock_telemetry_producer, mock_asyncio_event):
    assert consumer_instance.topic == os.getenv("QUEUE_CONTROL_TOPIC")
    assert consumer_instance.bootstrap_servers == os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    assert consumer_instance.username == os.getenv("KAFKA_USER")
    assert consumer_instance.password == os.getenv("KAFKA_PASSWORD")
    assert os.path.exists(consumer_instance.ca_path)
    assert consumer_instance.group_id == f"consumer-{os.getenv('QUEUE_ID')}"
    assert consumer_instance.queue_id == os.getenv("QUEUE_ID")
    assert consumer_instance.telemetry == mock_telemetry_producer
    assert consumer_instance.exit_on_ping is False
    assert consumer_instance.shutdown_event == mock_asyncio_event
    assert consumer_instance.consumer is None
    assert consumer_instance._task is None

def test_consumer_init_with_exit_on_ping(mock_telemetry_producer, mock_asyncio_event):
    consumer = KafkaCommandConsumer(
        queue_id="test_queue_id",
        telemetry_producer=mock_telemetry_producer,
        exit_on_ping=True,
        shutdown_event=mock_asyncio_event
    )
    assert consumer.exit_on_ping is True

def test_consumer_init_without_shutdown_event(mock_telemetry_producer):
    consumer = KafkaCommandConsumer(
        queue_id="test_queue_id",
        telemetry_producer=mock_telemetry_producer,
        exit_on_ping=False
    )
    assert isinstance(consumer.shutdown_event, asyncio.Event)

# Test start method
@pytest.mark.asyncio
async def test_consumer_start(consumer_instance, mock_ssl_context):
    await consumer_instance.start()

    mock_ssl_context.assert_called_once_with(ssl.PROTOCOL_TLS_CLIENT)
    mock_ssl_context.return_value.verify_mode = ssl.CERT_REQUIRED
    mock_ssl_context.return_value.load_verify_locations.assert_called_once_with(cafile=consumer_instance.ca_path)

    consumer_instance.mock_consumer_class.assert_called_once_with(
        consumer_instance.topic,
        bootstrap_servers=consumer_instance.bootstrap_servers,
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-512",
        sasl_plain_username=consumer_instance.username,
        sasl_plain_password=consumer_instance.password,
        ssl_context=mock_ssl_context.return_value,
        group_id=consumer_instance.group_id,
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )
    consumer_instance.mock_consumer_instance.start.assert_called_once()
    assert consumer_instance._task is not None
    assert isinstance(consumer_instance._task, asyncio.Task)

# Test stop method
@pytest.mark.asyncio
async def test_consumer_stop(consumer_instance, mock_aiokafka_consumer):
    consumer_instance.consumer = mock_aiokafka_consumer
    
    async def dummy_task():
        await asyncio.sleep(1)

    task = asyncio.create_task(dummy_task())
    consumer_instance._task = task

    await consumer_instance.stop()

    assert task.cancelled()
    mock_aiokafka_consumer.stop.assert_called_once()