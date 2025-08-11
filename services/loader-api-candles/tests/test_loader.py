import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# Import functions from loader.py
from app.loader import _parse_time_range, _process_kline, _get_next_start_time, run_loader

# Mock the config module
@pytest.fixture
def mock_config():
    with patch('app.config') as mock_cfg:
        mock_cfg.SYMBOL = "BTCUSDT"
        mock_cfg.INTERVAL = "1h"
        mock_cfg.TIME_RANGE = "2023-01-01:2023-01-02"
        mock_cfg.BINANCE_API_KEY = "test_key"
        mock_cfg.BINANCE_API_SECRET = "test_secret"
        mock_cfg.KAFKA_TOPIC = "test_topic"
        yield mock_cfg

# Mock the TelemetryProducer
@pytest.fixture
def mock_telemetry_producer():
    return AsyncMock()

# Mock the KafkaDataProducer
@pytest.fixture
def mock_kafka_producer():
    return AsyncMock()

# Mock the BinanceAPIClient
@pytest.fixture
def mock_binance_api_client():
    return AsyncMock()

@pytest.fixture
def mock_stop_event():
    return AsyncMock(spec=asyncio.Event)


# Test _parse_time_range
def test_parse_time_range():
    start_ms, end_ms = _parse_time_range("2023-01-01:2023-01-02")
    assert start_ms == int(datetime(2023, 1, 1).timestamp() * 1000)
    assert end_ms == int(datetime(2023, 1, 2).timestamp() * 1000)

# Test _process_kline
def test_process_kline():
    kline_data = [
        1672531200000, "16541.23", "16542.88", "16540.99", "16541.98",
        "123.45", 1672531259999, "2042134.56", 456, "60.12", "994512.34",
        "1000", "2000", "3000", "4000", "5000", "6000", "7000", "8000", "9000"
    ]
    symbol = "TESTSYM"
    interval = "1m"
    processed_data = _process_kline(kline_data, symbol, interval)

    assert processed_data["open_time"] == 1672531200000
    assert processed_data["open"] == 16541.23
    assert processed_data["symbol"] == "TESTSYM"
    assert processed_data["interval"] == "1m"

# Test _get_next_start_time
def test_get_next_start_time_with_klines():
    klines = [[0,0,0,0,0,0, 1672531259999]] # Mock kline with close_time
    next_time = _get_next_start_time(klines, 0, "1h")
    assert next_time == 1672531259999 + 1

def test_get_next_start_time_no_klines_1h():
    next_time = _get_next_start_time([], 1000, "1h")
    assert next_time == 1000 + 3600 * 1000

def test_get_next_start_time_no_klines_1m():
    next_time = _get_next_start_time([], 1000, "1m")
    assert next_time == 1000 + 60 * 1000

# Test run_loader (integration with mocks)
@pytest.mark.asyncio
async def test_run_loader_success(
    mock_config,
    mock_telemetry_producer,
    mock_kafka_producer,
    mock_binance_api_client,
    mock_stop_event
):
    # Mock API client to return some klines
    mock_binance_api_client.get_klines.return_value = [
        [1672531200000, "10", "11", "9", "10", "1", 1672531259999, "1", 1, "1", "1"],
        [1672531260000, "10", "11", "9", "10", "1", 1672531319999, "1", 1, "1", "1"],
    ]
    mock_stop_event.is_set.side_effect = [False, False, False, True] # Stop after a few iterations

    with (
        patch('app.loader.BinanceAPIClient', return_value=mock_binance_api_client),
        patch('app.loader.KafkaDataProducer', return_value=mock_kafka_producer)
    ):
        await run_loader(mock_stop_event, mock_telemetry_producer)

    # Assertions
    mock_binance_api_client.get_klines.assert_called()
    mock_kafka_producer.send.assert_called()
    mock_telemetry_producer.send_status_update.assert_called()
    mock_kafka_producer.start.assert_called_once()
    mock_kafka_producer.stop.assert_called_once()
    mock_binance_api_client.close.assert_called_once()

@pytest.mark.asyncio
async def test_run_loader_stop_event(
    mock_config,
    mock_telemetry_producer,
    mock_kafka_producer,
    mock_binance_api_client,
    mock_stop_event
):
    mock_binance_api_client.get_klines.return_value = [
        [1672531200000, "10", "11", "9", "10", "1", 1672531259999, "1", 1, "1", "1"],
    ]
    mock_stop_event.is_set.return_value = True # Stop immediately

    with (
        patch('app.loader.BinanceAPIClient', return_value=mock_binance_api_client),
        patch('app.loader.KafkaDataProducer', return_value=mock_kafka_producer)
    ):
        await run_loader(mock_stop_event, mock_telemetry_producer)

    mock_kafka_producer.send.assert_not_called() # Should not send if stopped immediately
    mock_telemetry_producer.send_status_update.assert_called_with(status="interrupted", message="Loader task cancelled.", finished=False, records_written=0)

@pytest.mark.asyncio
async def test_run_loader_api_error(
    mock_config,
    mock_telemetry_producer,
    mock_kafka_producer,
    mock_binance_api_client,
    mock_stop_event
):
    mock_binance_api_client.get_klines.side_effect = RuntimeError("API Error")
    mock_stop_event.is_set.return_value = False # Ensure stop_event is not set

    with (
        patch('app.loader.BinanceAPIClient', return_value=mock_binance_api_client),
        patch('app.loader.KafkaDataProducer', return_value=mock_kafka_producer)
    ):
        await run_loader(mock_stop_event, mock_telemetry_producer)

    mock_telemetry_producer.send_status_update.assert_called_with(status="error", message="Fatal loader error", error_message="API Error", finished=False, records_written=0)
    mock_kafka_producer.send.assert_not_called()