import pytest
import os
from unittest.mock import patch
from importlib import reload

# We need to re-import config after patching os.getenv
# to ensure the module-level os.getenv calls are mocked.
# This is a common pattern when testing module-level constants.

@pytest.fixture(autouse=True)
def mock_os_getenv():
    with patch('os.getenv') as mock_getenv:
        yield mock_getenv

def test_config_all_env_vars_set(mock_os_getenv):
    mock_os_getenv.side_effect = lambda key, default=None: {
        "QUEUE_ID": "mock_queue_id",
        "SYMBOL": "mock_symbol",
        "TYPE": "mock_type",
        "KAFKA_TOPIC": "mock_kafka_topic",
        "TIME_RANGE": "mock_time_range",
        "INTERVAL": "mock_interval",
        "KAFKA_BOOTSTRAP_SERVERS": "mock_kafka_servers",
        "KAFKA_USER": "mock_kafka_user",
        "KAFKA_PASSWORD": "mock_kafka_password",
        "KAFKA_CA_PATH": "mock_kafka_ca_path",
        "QUEUE_CONTROL_TOPIC": "mock_control_topic",
        "QUEUE_EVENTS_TOPIC": "mock_events_topic",
        "BINANCE_API_KEY": "mock_binance_api_key",
        "BINANCE_API_SECRET": "mock_binance_api_secret",
        "TELEMETRY_PRODUCER_ID": "mock_telemetry_id",
        "K8S_NAMESPACE": "mock_k8s_namespace",
        "ARANGO_URL": "mock_arango_url",
        "ARANGO_DB": "mock_arango_db",
        "LOADER_IMAGE": "mock_loader_image",
        "CONSUMER_IMAGE": "mock_consumer_image",
    }.get(key, default)

    # Import config AFTER patching os.getenv
    import app.config as config
    reload(config)

    assert config.QUEUE_ID == "mock_queue_id"
    assert config.SYMBOL == "mock_symbol"
    assert config.TYPE == "mock_type"
    assert config.KAFKA_TOPIC == "mock_kafka_topic"
    assert config.TIME_RANGE == "mock_time_range"
    assert config.INTERVAL == "mock_interval"
    assert config.KAFKA_BOOTSTRAP_SERVERS == "mock_kafka_servers"
    assert config.KAFKA_USER == "mock_kafka_user"
    assert config.KAFKA_PASSWORD == "mock_kafka_password"
    assert config.KAFKA_CA_PATH == "mock_kafka_ca_path"
    assert config.QUEUE_CONTROL_TOPIC == "mock_control_topic"
    assert config.QUEUE_EVENTS_TOPIC == "mock_events_topic"
    assert config.BINANCE_API_KEY == "mock_binance_api_key"
    assert config.BINANCE_API_SECRET == "mock_binance_api_secret"
    assert config.TELEMETRY_PRODUCER_ID == "mock_telemetry_id"
    assert config.K8S_NAMESPACE == "mock_k8s_namespace"
    assert config.ARANGO_URL == "mock_arango_url"
    assert config.ARANGO_DB == "mock_arango_db"
    assert config.LOADER_IMAGE == "mock_loader_image"
    assert config.CONSUMER_IMAGE == "mock_consumer_image"

def test_config_missing_env_vars_with_defaults(mock_os_getenv):
    mock_os_getenv.side_effect = lambda key, default=None: {
        "QUEUE_ID": "mock_queue_id",
        "SYMBOL": "mock_symbol",
        "TYPE": "mock_type",
        "KAFKA_TOPIC": "mock_kafka_topic",
        "TIME_RANGE": "mock_time_range",
        # INTERVAL has a default in config.py
        "KAFKA_BOOTSTRAP_SERVERS": "mock_kafka_servers",
        "KAFKA_USER": "mock_kafka_user",
        "KAFKA_PASSWORD": "mock_kafka_password",
        "KAFKA_CA_PATH": "mock_kafka_ca_path",
        # QUEUE_CONTROL_TOPIC has a default in config.py
        # QUEUE_EVENTS_TOPIC has a default in config.py
        "BINANCE_API_KEY": "mock_binance_api_key",
        "BINANCE_API_SECRET": "mock_binance_api_secret",
        "TELEMETRY_PRODUCER_ID": "mock_telemetry_id",
        # K8S_NAMESPACE, ARANGO_URL, ARANGO_DB, LOADER_IMAGE, CONSUMER_IMAGE have no defaults
    }.get(key, default)

    import app.config as config
    reload(config)

    assert config.QUEUE_ID == "mock_queue_id"
    assert config.SYMBOL == "mock_symbol"
    assert config.TYPE == "mock_type"
    assert config.KAFKA_TOPIC == "mock_kafka_topic"
    assert config.TIME_RANGE == "mock_time_range"
    assert config.INTERVAL == "1h" # Default value
    assert config.KAFKA_BOOTSTRAP_SERVERS == "mock_kafka_servers"
    assert config.KAFKA_USER == "mock_kafka_user"
    assert config.KAFKA_PASSWORD == "mock_kafka_password"
    assert config.KAFKA_CA_PATH == "mock_kafka_ca_path"
    assert config.QUEUE_CONTROL_TOPIC == "queue-control" # Default value
    assert config.QUEUE_EVENTS_TOPIC == "queue-events" # Default value
    assert config.BINANCE_API_KEY == "mock_binance_api_key"
    assert config.BINANCE_API_SECRET == "mock_binance_api_secret"
    assert config.TELEMETRY_PRODUCER_ID == "mock_telemetry_id"
    assert config.K8S_NAMESPACE is None
    assert config.ARANGO_URL is None
    assert config.ARANGO_DB is None
    assert config.LOADER_IMAGE is None
    assert config.CONSUMER_IMAGE is None

def test_config_missing_all_env_vars(mock_os_getenv):
    mock_os_getenv.side_effect = lambda key, default=None: default # Simulate missing env vars, allowing os.getenv defaults

    import app.config as config
    reload(config)

    assert config.QUEUE_ID is None
    assert config.SYMBOL is None
    assert config.TYPE is None
    assert config.KAFKA_TOPIC is None
    assert config.TIME_RANGE is None
    assert config.INTERVAL == "1h" # Default value
    assert config.KAFKA_BOOTSTRAP_SERVERS is None
    assert config.KAFKA_USER is None
    assert config.KAFKA_PASSWORD is None
    assert config.KAFKA_CA_PATH is None
    assert config.QUEUE_CONTROL_TOPIC == "queue-control" # Default value
    assert config.QUEUE_EVENTS_TOPIC == "queue-events" # Default value
    assert config.BINANCE_API_KEY is None
    assert config.BINANCE_API_SECRET is None
    assert config.TELEMETRY_PRODUCER_ID is None
    assert config.K8S_NAMESPACE is None
    assert config.ARANGO_URL is None
    assert config.ARANGO_DB is None
    assert config.LOADER_IMAGE is None
    assert config.CONSUMER_IMAGE is None
