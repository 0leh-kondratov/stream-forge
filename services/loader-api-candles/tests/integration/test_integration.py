import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.loader import run_loader
from app import config

# Mock the config module for integration tests
@pytest.fixture
def mock_integration_config():
    with patch('app.config') as mock_cfg:
        mock_cfg.SYMBOL = "TESTSYM"
        mock_cfg.INTERVAL = "1m"
        mock_cfg.TIME_RANGE = "2023-01-01:2023-01-01" # A single day for simplicity
        mock_cfg.BINANCE_API_KEY = "test_key"
        mock_cfg.BINANCE_API_SECRET = "test_secret"
        mock_cfg.KAFKA_TOPIC = "test_topic"
        yield mock_cfg

# Mock the TelemetryProducer for integration tests
@pytest.fixture
def mock_integration_telemetry_producer():
    return AsyncMock()

# Mock the KafkaDataProducer for integration tests
@pytest.fixture
def mock_integration_kafka_producer():
    mock = AsyncMock()
    mock.sent_messages = [] # To store messages sent
    async def mock_send(message):
        mock.sent_messages.append(message)
    mock.send.side_effect = mock_send
    return mock

# Mock the BinanceAPIClient for integration tests
@pytest.fixture
def mock_integration_binance_api_client():
    mock = AsyncMock()
    # Simulate a single kline for a simple test
    mock.get_klines.return_value = [
        [1672531200000, "100", "101", "99", "100", "10", 1672531259999, "20", 1, "5", "10"],
    ]
    return mock

@pytest.fixture
def mock_integration_stop_event():
    mock = AsyncMock(spec=asyncio.Event)
    mock.is_set.return_value = False # Ensure it doesn't stop prematurely
    return mock

@pytest.mark.asyncio
async def test_loader_full_data_flow(
    mock_integration_config,
    mock_integration_telemetry_producer,
    mock_integration_kafka_producer,
    mock_integration_binance_api_client,
    mock_integration_stop_event
):
    """
    Tests the full data flow from fetching klines to publishing to Kafka.
    This is an integration-like test using mocks for external services.
    """
    with (
        patch('app.loader.BinanceAPIClient', return_value=mock_integration_binance_api_client),
        patch('app.loader.KafkaDataProducer', return_value=mock_integration_kafka_producer)
    ):
        await run_loader(mock_integration_stop_event, mock_integration_telemetry_producer)

    # Assertions
    mock_integration_binance_api_client.get_klines.assert_called_once()
    mock_integration_kafka_producer.start.assert_called_once()
    mock_integration_kafka_producer.stop.assert_called_once()
    mock_integration_binance_api_client.close.assert_called_once()

    # Verify messages sent to Kafka
    assert len(mock_integration_kafka_producer.sent_messages) == 1
    sent_message = mock_integration_kafka_producer.sent_messages[0]

    assert sent_message["open_time"] == 1672531200000
    assert sent_message["open"] == 100.0
    assert sent_message["symbol"] == "TESTSYM"
    assert sent_message["interval"] == "1m"

    # Verify telemetry updates
    mock_integration_telemetry_producer.send_status_update.assert_any_call(
        status="started", message="Loader started, fetching historical data."
    )
    mock_integration_telemetry_producer.send_status_update.assert_any_call(
        status="loading", message="Fetched 1 and published 1 records.", records_written=1
    )
    mock_integration_telemetry_producer.send_status_update.assert_any_call(
        status="finished", message="Loader finished. Total records published: 1", finished=True, records_written=1
    )
