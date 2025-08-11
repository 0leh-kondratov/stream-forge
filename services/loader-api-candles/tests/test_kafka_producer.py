import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import json

from app.kafka_producer import KafkaDataProducer

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
        mock_cfg.KAFKA_PASSWORD = "testpass"
        mock_cfg.CA_PATH = "/tmp/ca.crt"
        mock_cfg.KAFKA_TOPIC = "test_topic"
        yield mock_cfg

@pytest.mark.asyncio
async def test_kafka_data_producer_start_stop(mock_kafka_producer_internal, mock_config):
    with patch('app.kafka_producer.AIOKafkaProducer', return_value=mock_kafka_producer_internal):
        producer = KafkaDataProducer()
        await producer.start()
        mock_kafka_producer_internal.start.assert_called_once()
        await producer.stop()
        mock_kafka_producer_internal.stop.assert_called_once()

@pytest.mark.asyncio
async def test_kafka_data_producer_send(mock_kafka_producer_internal, mock_config):
    with patch('app.kafka_producer.AIOKafkaProducer', return_value=mock_kafka_producer_internal):
        producer = KafkaDataProducer()
        await producer.start()
        
        test_data = {"key": "value", "number": 123}
        await producer.send(test_data)
        
        mock_kafka_producer_internal.send_and_wait.assert_called_once_with(
            mock_config.KAFKA_TOPIC, json.dumps(test_data).encode('utf-8')
        )
        await producer.stop()
