import pytest
import asyncio
import websockets
import httpx
import os

# Assuming the visualizer service is running at http://localhost:8000
BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_websocket_connection():
    # This test requires the visualizer service to be running
    # and a Kafka topic to be available.
    # For a real integration test, you'd mock Kafka or run a test Kafka instance.
    test_topic = "test-visualizer-topic"
    ws_url = f"ws://localhost:8000/ws/topic/{test_topic}"
    try:
        async with websockets.connect(ws_url) as websocket:
            await websocket.send("Hello from test client")
            response = await websocket.recv()
            assert "Hello from test client" in response # Or whatever the service echoes/processes
    except ConnectionRefusedError:
        pytest.skip("Visualizer service not running or WebSocket not available.")

@pytest.mark.asyncio
async def test_get_candles_data():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/data/candles/BTCUSDT")
        assert response.status_code == 200
        assert "Candles data for BTCUSDT" in response.text

# Add more integration tests for Kafka consumption, ArangoDB interaction, etc.
