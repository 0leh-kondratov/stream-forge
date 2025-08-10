import pytest
import os
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.kafka_consumer import KafkaCommandConsumer
from app.metrics import dummy_pings_total, dummy_pongs_total

# Mock environment variables
@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict(os.environ, {
        "QUEUE_CONTROL_TOPIC": "test-topic",
        "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
        "KAFKA_USER": "testuser",
        "KAFKA_PASSWORD": "testpassword",
        "KAFKA_CA_PATH": "/etc/ssl/certs/ca.crt"
    }):
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
    mock = AsyncMock()
    mock.start = AsyncMock()
    mock.stop = AsyncMock()
    mock.__aiter__ = AsyncMock()
    mock.__aiter__.return_value = [] # Default to no messages
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
def consumer_instance(mock_telemetry_producer, mock_asyncio_event):
    return KafkaCommandConsumer(
        queue_id="test_queue_id",
        telemetry_producer=mock_telemetry_producer,
        exit_on_ping=False,
        shutdown_event=mock_asyncio_event
    )

# Test __init__
def test_consumer_init(consumer_instance, mock_telemetry_producer, mock_asyncio_event):
    assert consumer_instance.topic == "test-topic"
    assert consumer_instance.bootstrap_servers == "localhost:9092"
    assert consumer_instance.username == "testuser"
    assert consumer_instance.password == "testpassword"
    assert consumer_instance.ca_path == "/etc/ssl/certs/ca.crt"
    assert consumer_instance.group_id == "consumer-test_queue_id"
    assert consumer_instance.queue_id == "test_queue_id"
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
    with patch('aiokafka.AIOKafkaConsumer') as MockAIOKafkaConsumer:
        mock_consumer_instance = MockAIOKafkaConsumer.return_value
        mock_consumer_instance.start = AsyncMock()
        mock_consumer_instance.stop = AsyncMock()
        mock_consumer_instance.__aiter__ = AsyncMock()

        await consumer_instance.start()

        mock_ssl_context.assert_called_once_with(ssl.PROTOCOL_TLS_CLIENT)
        mock_ssl_context.return_value.verify_mode = ssl.CERT_REQUIRED
        mock_ssl_context.return_value.load_verify_locations.assert_called_once_with(cafile="/etc/ssl/certs/ca.crt")

        MockAIOKafkaConsumer.assert_called_once_with(
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
        mock_consumer_instance.start.assert_called_once()
        assert consumer_instance._task is not None
        assert isinstance(consumer_instance._task, asyncio.Task)

# Test stop method
@pytest.mark.asyncio
async def test_consumer_stop(consumer_instance, mock_aiokafka_consumer):
    consumer_instance.consumer = mock_aiokafka_consumer
    
    with patch('asyncio.create_task') as mock_create_task:
        mock_task = MagicMock()
        mock_task.cancel = MagicMock()
        mock_task.done = MagicMock(return_value=True)
        mock_create_task.return_value = mock_task
        consumer_instance._task = mock_task # Assign the mocked task

        await consumer_instance.stop()

        mock_task.cancel.assert_called_once()
        mock_aiokafka_consumer.stop.assert_called_once()
        assert mock_task.done() # Task should be cancelled and done

@pytest.mark.asyncio
async def test_consumer_stop_no_task_no_consumer(consumer_instance):
    consumer_instance.consumer = None
    consumer_instance._task = None
    await consumer_instance.stop() # Should not raise error

# Test consume method - ping command
@pytest.mark.asyncio
async def test_consume_ping_command_matching_id(consumer_instance, mock_aiokafka_consumer, mock_metrics):
    message_value = json.dumps({
        "command": "ping",
        "queue_id": "test_queue_id",
        "sent_at": 12345.67
    }).encode('utf-8')
    mock_msg = MagicMock(value=message_value)
    # Correct way to mock async for iteration
    async def async_gen():
        yield mock_msg
    mock_aiokafka_consumer.__aiter__.return_value = async_gen() # Return an async generator

    consumer_instance.consumer = mock_aiokafka_consumer
    consumer_instance._task = asyncio.create_task(consumer_instance.consume())

    await consumer_instance._task # Give consume loop a chance to run

    mock_metrics.dummy_pings_total.inc.assert_called_once()
    consumer_instance.telemetry.send_event.assert_called_once_with(
        "pong",
        {
            "ping_ts": 12345.67,
            "ponged_at": pytest.approx(time.time(), abs=0.1),
            "queue_id": "test_queue_id",
        }
    )
    mock_metrics.dummy_pongs_total.inc.assert_called_once()
    consumer_instance.shutdown_event.set.assert_not_called() # exit_on_ping is False

@pytest.mark.asyncio
async def test_consume_ping_command_exit_on_ping(mock_telemetry_producer, mock_aiokafka_consumer, mock_asyncio_event, mock_metrics):
    consumer_instance = KafkaCommandConsumer(
        queue_id="test_queue_id",
        telemetry_producer=mock_telemetry_producer,
        exit_on_ping=True,
        shutdown_event=mock_asyncio_event
    )
    message_value = json.dumps({
        "command": "ping",
        "queue_id": "test_queue_id",
        "sent_at": 12345.67
    }).encode('utf-8')
    mock_msg = MagicMock(value=message_value)
    # Correct way to mock async for iteration
    async def async_gen():
        yield mock_msg
    mock_aiokafka_consumer.__aiter__.return_value = async_gen() # Return an async generator

    consumer_instance.consumer = mock_aiokafka_consumer
    consumer_instance._task = asyncio.create_task(consumer_instance.consume())

    await consumer_instance._task # Give consume loop a chance to run

    mock_metrics.dummy_pings_total.inc.assert_called_once()
    mock_telemetry_producer.send_event.assert_called_once()
    mock_metrics.dummy_pongs_total.inc.assert_called_once()
    mock_asyncio_event.set.assert_called_once() # Should set shutdown event

@pytest.mark.asyncio
async def test_consume_ping_command_non_matching_id(consumer_instance, mock_aiokafka_consumer, mock_metrics):
    message_value = json.dumps({
        "command": "ping",
        "queue_id": "other_queue_id",
        "sent_at": 12345.67
    }).encode('utf-8')
    mock_msg = MagicMock(value=message_value)
    # Correct way to mock async for iteration
    async def async_gen():
        yield mock_msg
    mock_aiokafka_consumer.__aiter__.return_value = async_gen() # Return an async generator

    consumer_instance.consumer = mock_aiokafka_consumer
    consumer_instance._task = asyncio.create_task(consumer_instance.consume())

    await consumer_instance._task # Give consume loop a chance to run

    mock_metrics.dummy_pings_total.inc.assert_not_called()
    consumer_instance.telemetry.send_event.assert_not_called()
    mock_metrics.dummy_pongs_total.inc.assert_not_called()

# Test consume method - stop command
@pytest.mark.asyncio
async def test_consume_stop_command(consumer_instance, mock_aiokafka_consumer, mock_asyncio_event):
    message_value = json.dumps({
        "command": "stop",
        "queue_id": "test_queue_id"
    }).encode('utf-8')
    mock_msg = MagicMock(value=message_value)
    # Correct way to mock async for iteration
    async def async_gen():
        yield mock_msg
    mock_aiokafka_consumer.__aiter__.return_value = async_gen() # Return an async generator

    consumer_instance.consumer = mock_aiokafka_consumer
    consumer_instance._task = asyncio.create_task(consumer_instance.consume())

    await consumer_instance._task # Give consume loop a chance to run

    consumer_instance.telemetry.send_status_update.assert_called_once_with(
        status="interrupted",
        message="Получена команда остановки",
        finished=True,
    )
    mock_asyncio_event.set.assert_called_once()

# Test consume method - error handling
@pytest.mark.asyncio
async def test_consume_invalid_json_message(consumer_instance, mock_aiokafka_consumer):
    mock_msg = MagicMock(value=b"invalid json")
    mock_aiokafka_consumer.__aiter__.return_value = [mock_msg]

    consumer_instance.consumer = mock_aiokafka_consumer
    consumer_instance._task = asyncio.create_task(consumer_instance.consume())

    with patch('loguru.logger.error') as mock_logger_error:
        await asyncio.sleep(0.1) # Give consume loop a chance to run
        mock_logger_error.assert_called_once()
        assert "Failed to process message" in mock_logger_error.call_args[0][0]

@pytest.mark.asyncio
async def test_consume_missing_command_or_target_id(consumer_instance, mock_aiokafka_consumer):
    message_value = json.dumps({
        "some_other_key": "value"
    }).encode('utf-8')
    mock_msg = MagicMock(value=message_value)
    # Correct way to mock async for iteration
    async def async_gen():
        yield mock_msg
    mock_aiokafka_consumer.__aiter__.return_value = async_gen() # Return an async generator

    consumer_instance.consumer = mock_aiokafka_consumer
    consumer_instance._task = asyncio.create_task(consumer_instance.consume())

    with patch('loguru.logger.debug') as mock_logger_debug:
        await asyncio.sleep(0.1) # Give consume loop a chance to run
        # Should log the received command, but not process it further
        mock_logger_debug.assert_called_once()
        assert "Received command" in mock_logger_debug.call_args[0][0]
        consumer_instance.telemetry.send_event.assert_not_called()
        consumer_instance.telemetry.send_status_update.assert_not_called()

@pytest.mark.asyncio
async def test_consume_asyncio_cancelled_error(consumer_instance, mock_aiokafka_consumer):
    mock_aiokafka_consumer.__aiter__.side_effect = asyncio.CancelledError
    consumer_instance.consumer = mock_aiokafka_consumer
    consumer_instance._task = asyncio.create_task(consumer_instance.consume())

    with patch('loguru.logger.warning') as mock_logger_warning:
        await asyncio.sleep(0.1) # Give consume loop a chance to run
        mock_logger_warning.assert_called_once()
        assert "Kafka consumer task cancelled" in mock_logger_warning.call_args[0][0]

@pytest.mark.asyncio
async def test_consume_general_exception_in_loop(consumer_instance, mock_aiokafka_consumer):
    mock_aiokafka_consumer.__aiter__.side_effect = Exception("Test exception")
    consumer_instance.consumer = mock_aiokafka_consumer
    consumer_instance._task = asyncio.create_task(consumer_instance.consume())

    with patch('loguru.logger.error') as mock_logger_error:
        await asyncio.sleep(0.1) # Give consume loop a chance to run
        mock_logger_error.assert_called_once()
        assert "Kafka consume loop failed" in mock_logger_error.call_args[0][0]
        assert "Test exception" in mock_logger_error.call_args[0][0]