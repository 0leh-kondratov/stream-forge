import pytest
import os
import asyncio
import json
import time
import ssl
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from arango import ArangoClient
from unittest.mock import patch
import httpx # For checking service health endpoint

# Environment variables for Kafka and ArangoDB are expected to be set in CI
# KAFKA_BOOTSTRAP_SERVERS
# KAFKA_USER
# KAFKA_PASSWORD
# KAFKA_CA_PATH
# ARANGO_URL
# ARANGO_DB
# ARANGO_USER (assuming)
# ARANGO_PASSWORD (assuming)
# QUEUE_EVENTS_TOPIC (assuming)
# QUEUE_CONTROL_TOPIC (assuming)
# QUEUE_ID (assuming)

# Fixture for Kafka Producer
@pytest.fixture(scope="module")
async def kafka_producer():
    ssl_context = ssl.create_default_context(cafile=os.getenv("KAFKA_CA_PATH"))
    producer = AIOKafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-512",
        sasl_plain_username=os.getenv("KAFKA_USER"),
        sasl_plain_password=os.getenv("KAFKA_PASSWORD"),
        ssl_context=ssl_context,
    )
    await producer.start()
    yield producer
    await producer.stop()

# Fixture for Kafka Consumer (for reading messages sent by the service)
@pytest.fixture(scope="module")
async def kafka_consumer():
    ssl_context = ssl.create_default_context(cafile=os.getenv("KAFKA_CA_PATH"))
    consumer = AIOKafkaConsumer(
        os.getenv("QUEUE_EVENTS_TOPIC", "queue-events"), # Assuming service sends events to this topic
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-512",
        sasl_plain_username=os.getenv("KAFKA_USER"),
        sasl_plain_password=os.getenv("KAFKA_PASSWORD"),
        ssl_context=ssl_context,
        group_id="integration_test_consumer_group",
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )
    await consumer.start()
    yield consumer
    await consumer.stop()

# Fixture for ArangoDB Client
@pytest.fixture(scope="module")
def arango_db_client():
    client = ArangoClient(hosts=os.getenv("ARANGO_URL"))
    db = client.db(
        os.getenv("ARANGO_DB"),
        username=os.getenv("ARANGO_USER"), # Assuming ARANGO_USER env var
        password=os.getenv("ARANGO_PASSWORD"), # Assuming ARANGO_PASSWORD env var
    )
    yield db

# Fixture for HTTP client to check service health
@pytest.fixture(scope="module")
async def http_client():
    async with httpx.AsyncClient() as client:
        yield client

# Test cases
@pytest.mark.asyncio
async def test_service_health_endpoint(http_client):
    """Test that the service's /metrics endpoint is reachable."""
    response = await http_client.get("http://localhost:8000/metrics")
    assert response.status_code == 200
    assert "dummy_pings_total" in response.text # Check for a known metric

@pytest.mark.asyncio
async def test_kafka_connectivity(kafka_producer):
    """Test that the Kafka producer can connect and send a message."""
    test_topic = os.getenv("QUEUE_CONTROL_TOPIC", "queue-control")
    message = {"test": "kafka_connectivity", "timestamp": time.time()}
    await kafka_producer.send_and_wait(test_topic, json.dumps(message).encode())
    # No assertion needed, just checking if send_and_wait raises an exception

@pytest.mark.asyncio
async def test_arango_connectivity(arango_db_client):
    """Test that the ArangoDB client can connect and list collections."""
    # This assumes the user has ARANGO_USER and ARANGO_PASSWORD set in CI
    # and that the database exists.
    collections = arango_db_client.collections()
    assert isinstance(collections, list)
    # No specific collection check, just basic connectivity

@pytest.mark.asyncio
async def test_service_processes_ping_command(kafka_producer, kafka_consumer, http_client):
    """
    Test that the dummy service processes a ping command and sends a pong.
    This requires the dummy service to be running and connected to Kafka.
    """
    control_topic = os.getenv("QUEUE_CONTROL_TOPIC", "queue-control")
    events_topic = os.getenv("QUEUE_EVENTS_TOPIC", "queue-events")
    queue_id = os.getenv("QUEUE_ID", "test_queue_id") # Assuming default queue_id for service

    # 1. Send a ping command to the service's control topic
    ping_payload = {
        "command": "ping",
        "queue_id": queue_id,
        "sent_at": time.time()
    }
    await kafka_producer.send_and_wait(control_topic, json.dumps(ping_payload).encode())

    # 2. Wait for the service to send a pong event
    pong_received = False
    # Set a timeout for the consumer loop
    timeout_start = time.time()
    async for msg in kafka_consumer:
        try:
            event_payload = json.loads(msg.value.decode())
            if event_payload.get("event") == "pong" and event_payload.get("queue_id") == queue_id:
                pong_received = True
                break
        except json.JSONDecodeError:
            pass # Ignore invalid JSON messages

        if time.time() - timeout_start > 15: # Increased timeout to 15 seconds
            break
    
    assert pong_received, "Событие Pong не было получено от сервиса"

    # 3. Verify metrics updated (optional, but good for integration)
    response = await http_client.get("http://localhost:8000/metrics")
    assert response.status_code == 200
    assert "dummy_pings_total" in response.text
    assert "dummy_pongs_total" in response.text
    # Further assertions could check the actual metric values if needed
