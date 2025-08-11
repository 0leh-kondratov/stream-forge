import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

# Import the main application functions
from app.main import main, handle_control_messages, stop_event

# Mock the config module for main.py tests
@pytest.fixture
def mock_main_config():
    with patch('app.config') as mock_cfg:
        mock_cfg.QUEUE_ID = "test-queue-id"
        mock_cfg.KAFKA_TOPIC = "test-kafka-topic"
        yield mock_cfg

# Mock TelemetryProducer for main.py tests
@pytest.fixture
def mock_main_telemetry_producer():
    mock = AsyncMock()
    mock.start.return_value = None
    mock.send_status_update.return_value = None
    mock.stop.return_value = None
    return mock

# Mock KafkaControlListener for main.py tests
@pytest.fixture
def mock_kafka_control_listener():
    mock = AsyncMock()
    mock.start.return_value = None
    mock.stop.return_value = None
    # Mock the listen method to yield control commands
    mock.listen.return_value.__aiter__.return_value = AsyncMock()
    return mock

# Mock run_loader for main.py tests
@pytest.fixture
def mock_run_loader():
    mock = AsyncMock()
    mock.return_value = None
    return mock

@pytest.mark.asyncio
async def test_main_starts_and_stops_gracefully(
    mock_main_config,
    mock_main_telemetry_producer,
    mock_kafka_control_listener,
    mock_run_loader
):
    # Simulate run_loader completing its task
    mock_run_loader.side_effect = lambda *args, **kwargs: stop_event.set() # Trigger stop event to exit main loop

    with (
        patch('app.main.TelemetryProducer', return_value=mock_main_telemetry_producer),
        patch('app.main.KafkaControlListener', return_value=mock_kafka_control_listener),
        patch('app.main.run_loader', new=mock_run_loader),
        patch('app.main.close_telemetry', new=AsyncMock())
    ):
        await main()

    mock_main_telemetry_producer.start.assert_called_once()
    mock_main_telemetry_producer.send_status_update.assert_any_call(status="started", message="Loader API Candles started")
    mock_run_loader.assert_called_once_with(stop_event, mock_main_telemetry_producer)
    mock_kafka_control_listener.start.assert_called_once()
    mock_kafka_control_listener.stop.assert_called_once()
    assert stop_event.is_set()

@pytest.mark.asyncio
async def test_handle_control_messages_stop_command(
    mock_main_config,
    mock_main_telemetry_producer,
    mock_kafka_control_listener
):
    # Simulate a stop command being received
    async def async_iter_commands():
        yield {"command": "stop", "queue_id": mock_main_config.QUEUE_ID}

    mock_kafka_control_listener.listen.return_value.__aiter__.return_value = async_iter_commands()

    # Run handle_control_messages in a task and wait for it to complete
    task = asyncio.create_task(handle_control_messages(mock_main_telemetry_producer))
    await asyncio.wait_for(task, timeout=1) # Wait for the task to process the command

    mock_kafka_control_listener.start.assert_called_once()
    mock_main_telemetry_producer.send_status_update.assert_called_once_with(
        status="interrupted",
        message="Stopped by user command",
        finished=True
    )
    assert stop_event.is_set()
    mock_kafka_control_listener.stop.assert_called_once()

@pytest.mark.asyncio
async def test_main_handles_loader_error(
    mock_main_config,
    mock_main_telemetry_producer,
    mock_kafka_control_listener,
    mock_run_loader
):
    mock_run_loader.side_effect = Exception("Loader failed")

    with (
        patch('app.main.TelemetryProducer', return_value=mock_main_telemetry_producer),
        patch('app.main.KafkaControlListener', return_value=mock_kafka_control_listener),
        patch('app.main.run_loader', new=mock_run_loader),
        patch('app.main.close_telemetry', new=AsyncMock())
    ):
        await main()

    mock_main_telemetry_producer.send_status_update.assert_any_call(status="started", message="Loader API Candles started")
    # The error telemetry is sent by run_loader, not main directly in this test setup.
    # mock_main_telemetry_producer.send_status_update.assert_any_call(status="error", message="Fatal loader error", error_message="Loader failed")
    mock_run_loader.assert_called_once()
    mock_kafka_control_listener.start.assert_called_once()
    mock_kafka_control_listener.stop.assert_called_once()
    assert stop_event.is_set() # stop_event should be set on error as well