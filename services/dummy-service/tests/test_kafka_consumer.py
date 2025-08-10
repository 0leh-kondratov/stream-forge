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
        "KAFKA_BOOTSTRAP_SERVERS": "k3-kafka-bootstrap.kafka:9093",
        "KAFKA_USER": "user-streamforge",
        "KAFKA_PASSWORD": "changeme",
        "KAFKA_CA_PATH": "/usr/local/share/ca-certificates/ca.crt"
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
    with patch('app.kafka_consumer.AIOKafkaConsumer') as MockAIOKafkaConsumer:
        mock_consumer_instance = MockAIOKafkaConsumer.return_value
        mock_consumer_instance.start = AsyncMock()
        mock_consumer_instance.stop = AsyncMock()
        mock_consumer_instance.__aiter__ = AsyncMock()
        mock_consumer_instance.__aiter__.return_value = [] # Default to no messages
        
        instance = KafkaCommandConsumer(
            queue_id="test_queue_id",
            telemetry_producer=mock_telemetry_producer,
            exit_on_ping=False,
            shutdown_event=mock_asyncio_event
        )
        # Attach the mock to the instance for access in tests
        instance.mock_consumer_class = MockAIOKafkaConsumer
        instance.mock_consumer_instance = mock_consumer_instance
        yield instance

# Test __init__
def test_consumer_init(consumer_instance, mock_telemetry_producer, mock_asyncio_event):
    assert consumer_instance.topic == "test-topic"
    assert consumer_instance.bootstrap_servers == "k3-kafka-bootstrap.kafka:9093"
    assert consumer_instance.username == "user-streamforge"
    assert consumer_instance.password == "changeme"
    assert consumer_instance.ca_path == "/usr/local/share/ca-certificates/ca.crt"
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
    await consumer_instance.start()

    mock_ssl_context.assert_called_once_with(ssl.PROTOCOL_TLS_CLIENT)
    mock_ssl_context.return_value.verify_mode = ssl.CERT_REQUIRED
    mock_ssl_context.return_value.load_verify_locations.assert_called_once_with(cafile="/usr/local/share/ca-certificates/ca.crt")

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
    mock_task = AsyncMock()
    consumer_instance._task = mock_task

    await consumer_instance.stop()

    mock_task.cancel.assert_called_once()
    mock_aiokafka_consumer.stop.assert_called_once()
    mock_task.__await__.assert_called_once()

@pytest.mark.asyncio
async def test_consumer_stop_no_task_no_consumer(consumer_instance):
    consumer_instance.consumer = None
    consumer_instance._task = None
    await consumer_instance.stop() # Should not raise error

# Test consume method - ping command
@pytest.mark.asyncio
async def test_consume_ping_command_matching_id(consumer_instance, mock_metrics):
    message_value = json.dumps({
        "command": "ping",
        "queue_id": "test_queue_id",
        "sent_at": 12345.67
    }).encode('utf-8')
    mock_msg = MagicMock(value=message_value)
    
    async def async_gen():
        yield mock_msg
    consumer_instance.mock_consumer_instance.__aiter__.return_value = async_gen()

    await consumer_instance.start()
    await consumer_instance._task

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
async def test_consume_ping_command_exit_on_ping(mock_telemetry_producer, mock_asyncio_event, mock_metrics):
    # Re-create a consumer instance with exit_on_ping=True
    with patch('app.kafka_consumer.AIOKafkaConsumer') as MockAIOKafkaConsumer:
        mock_consumer_instance = MockAIOKafkaConsumer.return_value
        mock_consumer_instance.start = AsyncMock()
        mock_consumer_instance.stop = AsyncMock()

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
        
        async def async_gen():
            yield mock_msg
        mock_consumer_instance.__aiter__.return_value = async_gen()

        await consumer_instance.start()
        await consumer_instance._task

        mock_metrics.dummy_pings_total.inc.assert_called_once()
        mock_telemetry_producer.send_event.assert_called_once()
        mock_metrics.dummy_pongs_total.inc.assert_called_once()
        mock_asyncio_event.set.assert_called_once() # Should set shutdown event

@pytest.mark.asyncio
async def test_consume_ping_command_non_matching_id(consumer_instance, mock_metrics):
    message_value = json.dumps({
        "command": "ping",
        "queue_id": "other_queue_id",
        "sent_at": 12345.67
    }).encode('utf-8')
    mock_msg = MagicMock(value=message_value)
    
    async def async_gen():
        yield mock_msg
    consumer_instance.mock_consumer_instance.__aiter__.return_value = async_gen()

    await consumer_instance.start()
    await consumer_instance._task

    mock_metrics.dummy_pings_total.inc.assert_not_called()
    consumer_instance.telemetry.send_event.assert_not_called()
    mock_metrics.dummy_pongs_total.inc.assert_not_called()

# Test consume method - stop command
@pytest.mark.asyncio
async def test_consume_stop_command(consumer_instance, mock_asyncio_event):
    message_value = json.dumps({
        "command": "stop",
        "queue_id": "test_queue_id"
    }).encode('utf-8')
    mock_msg = MagicMock(value=message_value)
    
    async def async_gen():
        yield mock_msg
    consumer_instance.mock_consumer_instance.__aiter__.return_value = async_gen()

    await consumer_instance.start()
    await consumer_instance._task

    consumer_instance.telemetry.send_status_update.assert_called_once_with(
        status="interrupted",
        message="Получена команда остановки",
        finished=True,
    )
    mock_asyncio_event.set.assert_called_once()

# Test consume method - error handling
@pytest.mark.asyncio
async def test_consume_invalid_json_message(consumer_instance):
    mock_msg = MagicMock(value=b"invalid json")
    
    async def async_gen():
        yield mock_msg
    consumer_instance.mock_consumer_instance.__aiter__.return_value = async_gen()

    with patch('loguru.logger.error') as mock_logger_error:
        await consumer_instance.start()
        await consumer_instance._task
        mock_logger_error.assert_called_once()
        assert "Failed to process message" in mock_logger_error.call_args[0][0]

@pytest.mark.asyncio
async def test_consume_missing_command_or_target_id(consumer_instance):
    message_value = json.dumps({
        "some_other_key": "value"
    }).encode('utf-8')
    mock_msg = MagicMock(value=message_value)

    async def async_gen():
        yield mock_msg
    consumer_instance.mock_consumer_instance.__aiter__.return_value = async_gen()

    with patch('loguru.logger.debug') as mock_logger_debug:
        await consumer_instance.start()
        await consumer_instance._task
        mock_logger_debug.assert_called()
        assert "Received command" in mock_logger_debug.call_args[0][0]
        consumer_instance.telemetry.send_event.assert_not_called()
        consumer_instance.telemetry.send_status_update.assert_not_called()

@pytest.mark.asyncio
async def test_consume_asyncio_cancelled_error(consumer_instance):
    consumer_instance.mock_consumer_instance.__aiter__.side_effect = asyncio.CancelledError

    with patch('loguru.logger.warning') as mock_logger_warning:
        await consumer_instance.start()
        await consumer_instance._task
        mock_logger_warning.assert_called_once()
        assert "Kafka consumer task cancelled" in mock_logger_warning.call_args[0][0]

@pytest.mark.asyncio
async def test_consume_general_exception_in_loop(consumer_instance):
    consumer_instance.mock_consumer_instance.__aiter__.side_effect = Exception("Test exception")

    with patch('loguru.logger.error') as mock_logger_error:
        await consumer_instance.start()
        await consumer_instance._task
        mock_logger_error.assert_called_once()
        assert "Kafka consume loop failed" in mock_logger_error.call_args[0][0]