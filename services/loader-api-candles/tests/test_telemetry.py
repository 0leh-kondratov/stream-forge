import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import json

from app.telemetry import TelemetryProducer, close_telemetry

@pytest.fixture
def mock_kafka_producer_internal():
    mock = AsyncMock()
    mock.start.return_value = None
    mock.stop.return_value = None
    mock.send_and_wait.return_value = None
    return mock

@pytest.fixture
def mock_config():
    with patch('app.config') as mock_cfg:
        mock_cfg.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
        mock_cfg.KAFKA_USER = "testuser"
        mock_cfg.Kafka_PASSWORD = "testpass"
        mock_cfg.CA_PATH = "/tmp/ca.crt"
        mock_cfg.QUEUE_EVENTS_TOPIC = "test_events_topic"
        mock_cfg.TELEMETRY_PRODUCER_ID = "test-telemetry-id"
        yield mock_cfg

@pytest.mark.asyncio
async def test_telemetry_producer_start_stop(mock_kafka_producer_internal, mock_config):
    with patch('app.telemetry.AIOKafkaProducer', return_value=mock_kafka_producer_internal):
        producer = TelemetryProducer()
        await producer.start()
        mock_kafka_producer_internal.start.assert_called_once()
        await producer.stop()
        mock_kafka_producer_internal.stop.assert_called_once()

@pytest.mark.asyncio
async def test_telemetry_producer_send_status_update(mock_kafka_producer_internal, mock_config):
    with patch('app.telemetry.AIOKafkaProducer', return_value=mock_kafka_producer_internal):
        producer = TelemetryProducer()
        await producer.start()
        
        await producer.send_status_update(
            status="started",
            message="Loader started",
            finished=False,
            records_written=0
        )
        
        # Assert that send_and_wait was called with the correct topic and a JSON-encoded message
        mock_kafka_producer_internal.send_and_wait.assert_called_once()
        args, kwargs = mock_kafka_producer_internal.send_and_wait.call_args
        
        assert args[0] == mock_config.QUEUE_EVENTS_TOPIC
        sent_message = json.loads(args[1].decode('utf-8'))
        
        assert sent_message["producer_id"] == mock_config.TELEMETRY_PRODUCER_ID
        assert sent_message["status"] == "started"
        assert sent_message["message"] == "Loader started"
        assert sent_message["finished"] == False
        assert sent_message["records_written"] == 0
        assert "timestamp" in sent_message

        await producer.stop()

@pytest.mark.asyncio
async def test_close_telemetry(mock_kafka_producer_internal, mock_config):
    with patch('app.telemetry.AIOKafkaProducer', return_value=mock_kafka_producer_internal):
        producer = TelemetryProducer()
        await producer.start()
        
        await close_telemetry(producer)
        mock_kafka_producer_internal.stop.assert_called_once()
