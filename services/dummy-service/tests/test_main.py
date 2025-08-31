import pytest
import os
import asyncio
import signal
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import parse_args, configure_logging, setup_signal_handlers, main
from app.kafka_consumer import KafkaCommandConsumer
from app.telemetry import TelemetryProducer, log_startup_event, simulate_loading, simulate_failure
from loguru import logger

# Fixtures for mocking dependencies
@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict(os.environ, {
        "QUEUE_ID": "test_queue_id",
        "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
        "KAFKA_USER": "testuser",
        "KAFKA_PASSWORD": "testpassword",
        "KAFKA_CA_PATH": "/etc/ssl/certs/ca.crt",
    }):
        yield

@pytest.fixture
def mock_telemetry_producer():
    mock = AsyncMock(spec=TelemetryProducer)
    mock.start = AsyncMock()
    mock.stop = AsyncMock()
    mock.send_status_update = AsyncMock()
    return mock

@pytest.fixture
def mock_kafka_consumer():
    mock = AsyncMock(spec=KafkaCommandConsumer)
    mock.start = AsyncMock()
    mock.stop = AsyncMock()
    return mock

@pytest.fixture
def mock_asyncio_event():
    mock = AsyncMock(spec=asyncio.Event)
    mock.wait = AsyncMock(return_value=None)
    mock.set = MagicMock()
    return mock

@pytest.fixture(autouse=True)
def mock_logger():
    with patch('loguru.logger.remove') as mock_remove,         patch('loguru.logger.add') as mock_add,         patch('loguru.logger.info') as mock_info:
        yield MagicMock(remove=mock_remove, add=mock_add, info=mock_info)

@pytest.fixture(autouse=True)
def mock_asyncio_tasks():
    with patch('asyncio.create_task') as mock_create_task, \
         patch('asyncio.sleep') as mock_sleep:
        yield MagicMock(create_task=mock_create_task, sleep=mock_sleep)

@pytest.fixture(autouse=True)
def mock_telemetry_functions():
    with patch('app.main.log_startup_event', new=AsyncMock()) as mock_log_startup_event, \
         patch('app.main.simulate_loading', new=AsyncMock()) as mock_simulate_loading, \
         patch('app.main.simulate_failure', new=AsyncMock()) as mock_simulate_failure:
        yield MagicMock(
            log_startup_event=mock_log_startup_event,
            simulate_loading=mock_simulate_loading,
            simulate_failure=mock_simulate_failure
        )

# Test parse_args
def test_parse_args_default():
    with patch('argparse.ArgumentParser.parse_args', return_value=MagicMock(debug=False, noop=False, exit_on_ping=False, exit_after=None, simulate_loading=False, fail_after=None)):
        args = parse_args()
        assert args.debug is False
        assert args.noop is False
        assert args.exit_on_ping is False
        assert args.exit_after is None
        assert args.simulate_loading is False
        assert args.fail_after is None

def test_parse_args_all_true():
    with patch('argparse.ArgumentParser.parse_args', return_value=MagicMock(debug=True, noop=True, exit_on_ping=True, exit_after=10, simulate_loading=True, fail_after=5)):
        args = parse_args()
        assert args.debug is True
        assert args.noop is True
        assert args.exit_on_ping is True
        assert args.exit_after == 10
        assert args.simulate_loading is True
        assert args.fail_after == 5

# Test configure_logging
def test_configure_logging_debug(mock_logger):
    configure_logging(True)
    mock_logger.remove.assert_called_once()
    mock_logger.add.assert_called_once()
    assert mock_logger.add.call_args[1]['level'] == "DEBUG"

def test_configure_logging_info(mock_logger):
    configure_logging(False)
    mock_logger.remove.assert_called_once()
    mock_logger.add.assert_called_once()
    assert mock_logger.add.call_args[1]['level'] == "INFO"

# Test setup_signal_handlers
def test_setup_signal_handlers(mock_asyncio_event):
    mock_loop = MagicMock()
    mock_loop.add_signal_handler = MagicMock()
    with patch('asyncio.get_event_loop', return_value=mock_loop):
        setup_signal_handlers(mock_asyncio_event)
        mock_loop.add_signal_handler.assert_any_call(signal.SIGTERM, mock_asyncio_event.set)
        mock_loop.add_signal_handler.assert_any_call(signal.SIGINT, mock_asyncio_event.set)

# Test main function scenarios
@pytest.mark.asyncio
async def test_main_basic_run_startup(
    mock_telemetry_producer,
    mock_kafka_consumer,
    mock_asyncio_event,
    mock_logger,
    mock_asyncio_tasks,
    mock_telemetry_functions
):
    """Tests the startup sequence of the main function."""
    with patch('app.main.parse_args', return_value=MagicMock(debug=False, noop=False, exit_on_ping=False, exit_after=None, simulate_loading=False, fail_after=None)), \
         patch('app.main.TelemetryProducer', return_value=mock_telemetry_producer), \
         patch('app.main.KafkaCommandConsumer', return_value=mock_kafka_consumer):
        
        logger.info("--- Running test_main_basic_run_startup ---")
        logger.info("Step 1: Running main function to test startup.")
        await main()

        logger.info("Step 2: Verifying startup procedures.")
        mock_telemetry_producer.start.assert_called_once()
        mock_telemetry_functions.log_startup_event.assert_called_once_with(mock_telemetry_producer)
        mock_kafka_consumer.start.assert_called_once()
        logger.info("--- Finished test_main_basic_run_startup ---")

@pytest.mark.asyncio
async def test_main_basic_run_wait(
    mock_telemetry_producer,
    mock_kafka_consumer,
    mock_asyncio_event,
    mock_logger,
    mock_asyncio_tasks,
    mock_telemetry_functions
):
    """Tests that the main function waits for the shutdown event."""
    with patch('app.main.parse_args', return_value=MagicMock(debug=False, noop=False, exit_on_ping=False, exit_after=None, simulate_loading=False, fail_after=None)), \
         patch('app.main.TelemetryProducer', return_value=mock_telemetry_producer), \
         patch('app.main.KafkaCommandConsumer', return_value=mock_kafka_consumer):
        
        logger.info("--- Running test_main_basic_run_wait ---")
        logger.info("Step 1: Running main function to test waiting.")
        await main()

        logger.info("Step 2: Verifying that main loop waits for shutdown.")
        mock_asyncio_event.wait.assert_called_once()
        logger.info("--- Finished test_main_basic_run_wait ---")

@pytest.mark.asyncio
async def test_main_basic_run_shutdown(
    mock_telemetry_producer,
    mock_kafka_consumer,
    mock_asyncio_event,
    mock_logger,
    mock_asyncio_tasks,
    mock_telemetry_functions
):
    """Tests the shutdown sequence of the main function."""
    with patch('app.main.parse_args', return_value=MagicMock(debug=False, noop=False, exit_on_ping=False, exit_after=None, simulate_loading=False, fail_after=None)), \
         patch('app.main.TelemetryProducer', return_value=mock_telemetry_producer), \
         patch('app.main.KafkaCommandConsumer', return_value=mock_kafka_consumer):
        
        logger.info("--- Running test_main_basic_run_shutdown ---")
        logger.info("Step 1: Running main function to test shutdown.")
        await main()

        logger.info("Step 2: Verifying shutdown procedures.")
        mock_kafka_consumer.stop.assert_called_once()
        mock_telemetry_producer.send_status_update.assert_called_once_with(
            status="finished",
            message="Микросервис завершил работу",
            finished=True,
            records_written=999
        )
        mock_telemetry_producer.stop.assert_called_once()
        logger.info("--- Finished test_main_basic_run_shutdown ---")


@pytest.mark.asyncio
async def test_main_noop_mode(
    mock_telemetry_producer,
    mock_kafka_consumer,
    mock_asyncio_event,
    mock_logger,
    mock_asyncio_tasks,
    mock_telemetry_functions
):
    with patch('app.main.parse_args', return_value=MagicMock(debug=False, noop=True, exit_on_ping=False, exit_after=None, simulate_loading=False, fail_after=None)), \
         patch('app.main.TelemetryProducer', return_value=mock_telemetry_producer), \
         patch('app.main.KafkaCommandConsumer', return_value=mock_kafka_consumer):
        
        await main()

        mock_telemetry_producer.start.assert_called_once()
        mock_telemetry_functions.log_startup_event.assert_called_once_with(mock_telemetry_producer)
        mock_kafka_consumer.start.assert_not_called()
        mock_logger.info.assert_any_call("Noop mode enabled — skipping Kafka consumer")
        mock_asyncio_event.wait.assert_called_once()
        mock_kafka_consumer.stop.assert_not_called()
        mock_telemetry_producer.send_status_update.assert_called_once()
        mock_telemetry_producer.stop.assert_called_once()

@pytest.mark.asyncio
async def test_main_exit_after(
    mock_telemetry_producer,
    mock_kafka_consumer,
    mock_asyncio_event,
    mock_logger,
    mock_asyncio_tasks,
    mock_telemetry_functions
):
    exit_time = 5
    with patch('app.main.parse_args', return_value=MagicMock(debug=False, noop=False, exit_on_ping=False, exit_after=exit_time, simulate_loading=False, fail_after=None)), \
         patch('app.main.TelemetryProducer', return_value=mock_telemetry_producer), \
         patch('app.main.KafkaCommandConsumer', return_value=mock_kafka_consumer):
        
        await main()

        mock_asyncio_tasks.sleep.assert_called_once_with(exit_time)
        mock_logger.info.assert_any_call(f"Exiting after {exit_time} seconds")
        mock_asyncio_event.set.assert_called_once()
        mock_asyncio_event.wait.assert_called_once()

@pytest.mark.asyncio
async def test_main_simulate_loading(
    mock_telemetry_producer,
    mock_kafka_consumer,
    mock_asyncio_event,
    mock_logger,
    mock_asyncio_tasks,
    mock_telemetry_functions
):
    with patch('app.main.parse_args', return_value=MagicMock(debug=False, noop=False, exit_on_ping=False, exit_after=None, simulate_loading=True, fail_after=None)), \
         patch('app.main.TelemetryProducer', return_value=mock_telemetry_producer), \
         patch('app.main.KafkaCommandConsumer', return_value=mock_kafka_consumer):
        
        await main()

        mock_asyncio_tasks.create_task.assert_any_call(mock_telemetry_functions.simulate_loading(mock_telemetry_producer))

@pytest.mark.asyncio
async def test_main_fail_after(
    mock_telemetry_producer,
    mock_kafka_consumer,
    mock_asyncio_event,
    mock_logger,
    mock_asyncio_tasks,
    mock_telemetry_functions
):
    fail_time = 3
    with patch('app.main.parse_args', return_value=MagicMock(debug=False, noop=False, exit_on_ping=False, exit_after=None, simulate_loading=False, fail_after=fail_time)), \
         patch('app.main.TelemetryProducer', return_value=mock_telemetry_producer), \
         patch('app.main.KafkaCommandConsumer', return_value=mock_kafka_consumer):
        
        await main()

        mock_asyncio_tasks.create_task.assert_any_call(mock_telemetry_functions.simulate_failure(fail_time, mock_telemetry_producer))

@pytest.mark.asyncio
async def test_main_exit_on_ping_passed_to_consumer(
    mock_telemetry_producer,
    mock_kafka_consumer,
    mock_asyncio_event,
    mock_logger,
    mock_asyncio_tasks,
    mock_telemetry_functions
):
    with patch('app.main.parse_args', return_value=MagicMock(debug=False, noop=False, exit_on_ping=True, exit_after=None, simulate_loading=False, fail_after=None)), \
         patch('app.main.TelemetryProducer', return_value=mock_telemetry_producer), \
         patch('app.main.KafkaCommandConsumer', return_value=mock_kafka_consumer) as MockKafkaCommandConsumerClass:
        
        await main()

        MockKafkaCommandConsumerClass.assert_called_once_with(
            queue_id=os.getenv("QUEUE_ID"),
            telemetry_producer=mock_telemetry_producer,
            exit_on_ping=True,
            shutdown_event=mock_asyncio_event,
        )
