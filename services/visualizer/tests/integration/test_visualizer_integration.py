import pytest
import asyncio
import httpx
import websockets
import os
import pytest_asyncio 
from app.settings import settings
from unittest.mock import AsyncMock # Import AsyncMock

# Define the base URL for the running application
BASE_URL = f"http://{settings.HOST}:{settings.PORT}"

@pytest_asyncio.fixture(scope="module")
async def running_app():
    # Set PYTHONPATH and TESTING for the subprocess
    env = os.environ.copy()
    env["PYTHONPATH"] = "/data/projects/stream-forge/services/visualizer"
    env["TESTING"] = "True" # Set TESTING environment variable

    process = None
    try:
        # Start the FastAPI application in a separate process
        process = await asyncio.create_subprocess_exec(
            "python3", "-m", "uvicorn", "app.main:app",
            "--host", settings.HOST, "--port", str(settings.PORT),
            env=env, 
            cwd="/data/projects/stream-forge/services/visualizer",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Give the server some time to start up
        await asyncio.sleep(5) 

        # Check if the server is actually running
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            response.raise_for_status()
            assert response.status_code == 200

        # Set return values for mocked ArangoDB client methods
        from app.main import arangodb_client as mocked_arangodb_client
        mocked_arangodb_client.fetch_candles = AsyncMock(return_value=[{"_key": "mock_candle", "value": 100}])
        mocked_arangodb_client.fetch_rsi = AsyncMock(return_value=[{"_key": "mock_rsi", "value": 70}])

        # Set return value for mocked Kafka consumer messages
        from app.main import kafka_manager as mocked_kafka_manager
        async def empty_async_generator():
            yield # This makes it an async generator that yields nothing
        mocked_kafka_manager.consume_messages = AsyncMock(return_value=empty_async_generator()) # Corrected mocking

        yield process

    except httpx.RequestError as e:
        print(f"Server did not start: {e}")
        if process:
            if process.stdout: 
                stdout_data = await process.stdout.read()
                print(f"Server stdout: {stdout_data.decode()}")
            if process.stderr: 
                stderr_data = await process.stderr.read()
                print(f"Server stderr: {stderr_data.decode()}")
            process.kill()
            await process.wait()
        raise
    except Exception as e:
        print(f"An unexpected error occurred during server startup: {e}")
        if process:
            process.kill()
            await process.wait()
        raise
    finally:
        # Teardown: Stop the application process
        if process and process.returncode is None:
            process.kill()
            await process.wait()

@pytest.mark.asyncio
async def test_health_check_integration(running_app):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_root_endpoint_integration(running_app):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/")
        assert response.status_code == 200
        assert "Hello from Visualizer!" in response.text # Updated assertion

@pytest.mark.asyncio
async def test_websocket_connection_integration(running_app):
    test_topic = "test-websocket-topic"
    ws_url = f"ws://{settings.HOST}:{settings.PORT}/ws/topic/{test_topic}"
    try:
        async with websockets.connect(ws_url) as websocket:
            assert websocket.state == websockets.protocol.State.OPEN # Corrected assertion
            # You might want to send a message and assert a response here
            # For now, just checking connection
    except Exception as e:
        pytest.fail(f"WebSocket connection failed: {e}")

# Note: For /candles and /rsi integration tests, you would need a running ArangoDB instance
# or mock the ArangoDB client within the running application, which is more complex.
# For now, we'll skip these or assume a running ArangoDB for true integration.
# For this example, we'll just test the endpoint existence.

@pytest.mark.asyncio
async def test_candles_endpoint_integration(running_app):
    async with httpx.AsyncClient(timeout=10.0) as client: # Increased timeout
        response = await client.get(f"{BASE_URL}/candles/some_collection/SOME_SYMBOL") # Reverted endpoint
        # Expecting 404 if ArangoDB is not running or data not found
        assert response.status_code == 200 # Expecting 200 now that return_value is set
        assert response.json() == [{"_key": "mock_candle", "value": 100}]

@pytest.mark.asyncio
async def test_rsi_endpoint_integration(running_app):
    async with httpx.AsyncClient(timeout=10.0) as client: # Increased timeout
        response = await client.get(f"{BASE_URL}/rsi/some_collection/SOME_SYMBOL") # Reverted endpoint
        # Expecting 404 if ArangoDB is not running or data not found
        assert response.status_code == 200 # Expecting 200 now that return_value is set
        assert response.json() == [{"_key": "mock_rsi", "value": 70}]