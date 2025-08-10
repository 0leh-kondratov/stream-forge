import pytest
import os
from unittest.mock import patch

# We need to re-import config after patching os.getenv
# to ensure the module-level os.getenv calls are mocked.
# This is a common pattern when testing module-level constants.

@pytest.fixture(autouse=True)
def mock_os_getenv():
    with patch('os.getenv') as mock_getenv:
        yield mock_getenv

def test_config_all_env_vars_set(mock_os_getenv):
    mock_os_getenv.side_effect = lambda key, default=None: {
        "KAFKA_BOOTSTRAP_SERVERS": "mock_kafka_servers",
        "KAFKA_USER": "mock_kafka_user",
        "KAFKA_PASSWORD": "mock_kafka_password",
        "CA_PATH": "mock_ca_path",
        "QUEUE_CONTROL_TOPIC": "mock_control_topic",
        "QUEUE_EVENTS_TOPIC": "mock_events_topic",
        "QUEUE_ID": "mock_queue_id",
        "SYMBOL": "mock_symbol",
        "TYPE": "mock_type",
        "INTERVAL": "mock_interval",
        "TIME_RANGE": "mock_time_range",
        "TELEMETRY_PRODUCER_ID": "mock_telemetry_id",
    }.get(key, default)

    # Import config AFTER patching os.getenv
    import app.config as config
    from importlib import reload
    reload(config)

    assert config.KAFKA_BOOTSTRAP_SERVERS == "mock_kafka_servers"
    assert config.KAFKA_USER == "mock_kafka_user"
    assert config.KAFKA_PASSWORD == "mock_kafka_password"
    assert config.CA_PATH == "mock_ca_path"
    assert config.QUEUE_CONTROL_TOPIC == "mock_control_topic"
    assert config.QUEUE_EVENTS_TOPIC == "mock_events_topic"
    assert config.QUEUE_ID == "mock_queue_id"
    assert config.SYMBOL == "mock_symbol"
    assert config.TYPE == "mock_type"
    assert config.INTERVAL == "mock_interval"
    assert config.TIME_RANGE == "mock_time_range"
    assert config.TELEMETRY_PRODUCER_ID == "mock_telemetry_id"

def test_config_missing_env_vars_with_defaults(mock_os_getenv):
    mock_os_getenv.side_effect = lambda key, default=None: {
        "KAFKA_BOOTSTRAP_SERVERS": "mock_kafka_servers",
        "KAFKA_USER": "mock_kafka_user",
        "KAFKA_PASSWORD": "mock_kafka_password",
        "CA_PATH": "mock_ca_path",
        "QUEUE_CONTROL_TOPIC": "mock_control_topic",
        "QUEUE_EVENTS_TOPIC": "mock_events_topic",
        "TIME_RANGE": "mock_time_range",
    }.get(key, default)

    import app.config as config
    from importlib import reload
    reload(config)

    assert config.KAFKA_BOOTSTRAP_SERVERS == "mock_kafka_servers"
    assert config.KAFKA_USER == "mock_kafka_user"
    assert config.KAFKA_PASSWORD == "mock_kafka_password"
    assert config.CA_PATH == "mock_ca_path"
    assert config.QUEUE_CONTROL_TOPIC == "mock_control_topic"
    assert config.QUEUE_EVENTS_TOPIC == "mock_events_topic"
    assert config.TIME_RANGE == "mock_time_range"

    # Check default values
    assert config.QUEUE_ID == "unknown-queue"
    assert config.SYMBOL == "BTCUSDT"
    assert config.TYPE == "api_candles_5m"
    assert config.TELEMETRY_PRODUCER_ID == "dummy-telemetry"

    # Check variables that should be None if not set and no default
    assert config.INTERVAL == "5m"

def test_config_missing_env_vars_without_defaults(mock_os_getenv):
    mock_os_getenv.side_effect = lambda key, default=None: {
        "QUEUE_ID": "mock_queue_id",
        "SYMBOL": "mock_symbol",
        "TYPE": "mock_type",
        "INTERVAL": "mock_interval",
        "TELEMETRY_PRODUCER_ID": "mock_telemetry_id",
    }.get(key, default)

    import app.config as config
    from importlib import reload
    reload(config)

    assert config.KAFKA_BOOTSTRAP_SERVERS is None
    assert config.KAFKA_USER is None
    assert config.KAFKA_PASSWORD is None
    assert config.CA_PATH is None
    assert config.QUEUE_CONTROL_TOPIC is None
    assert config.QUEUE_EVENTS_TOPIC is None
    assert config.TIME_RANGE is None

    # Check default values are still applied if not overridden
    assert config.QUEUE_ID == "mock_queue_id"
    assert config.SYMBOL == "mock_symbol"
    assert config.TYPE == "mock_type"
    assert config.TELEMETRY_PRODUCER_ID == "mock_telemetry_id"
