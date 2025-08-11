import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import json

from app.kafka_control import KafkaControlListener

@pytest.fixture
def mock_kafka_consumer_internal():
    mock = AsyncMock()
    mock.start.return_value = None
    mock.stop.return_value = None
    return mock

@pytest.fixture
def mock_config():
    with patch('app.config') as mock_cfg:
        mock_cfg.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
        mock_cfg.KAFKA_USER = "testuser"
        mock_cfg.KAFKA_PASSWORD = "testpass"
        mock_cfg.CA_PATH = "/tmp/ca.crt"
        mock_cfg.QUEUE_CONTROL_TOPIC = "test_control_topic"
        yield mock_cfg

@pytest.mark.asyncio
async def test_kafka_control_listener_start_stop(mock_kafka_consumer_internal, mock_config):
    with patch('app.kafka_control.AIOKafkaConsumer', return_value=mock_kafka_consumer_internal):
        listener = KafkaControlListener("test-queue-id")
        await listener.start()
        mock_kafka_consumer_internal.start.assert_called_once()
        await listener.stop()
        mock_kafka_consumer_internal.stop.assert_called_once()

@pytest.mark.asyncio
async def test_kafka_control_listener_listen_command(mock_kafka_consumer_internal, mock_config):
    test_command = {"command": "stop", "queue_id": "test-queue-id"}
    mock_msg = AsyncMock()
    mock_msg.value = json.dumps(test_command).encode('utf-8')

    async def mock_consumer_aiter():
        yield mock_msg

    mock_kafka_consumer_internal.__aiter__.return_value = mock_consumer_aiter()

    with patch('app.kafka_control.AIOKafkaConsumer', return_value=mock_kafka_consumer_internal):
        listener = KafkaControlListener("test-queue-id")
        await listener.start()
        
        commands = []
        async for cmd in listener.listen():
            commands.append(cmd)
            break # Only process one command for this test
        
        assert commands == [test_command]
        mock_kafka_consumer_internal.start.assert_called_once()
        await listener.stop()
