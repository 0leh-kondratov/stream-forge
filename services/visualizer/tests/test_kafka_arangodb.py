import pytest
from unittest.mock import AsyncMock, patch
from app.main import app, startup_event, shutdown_event # Import startup_event and shutdown_event
from httpx import AsyncClient

@pytest.fixture
def mock_kafka_manager():
    with patch('app.main.kafka_manager', new_callable=AsyncMock) as mock_manager:
        yield mock_manager

@pytest.fixture
def mock_arangodb_client():
    with patch('app.main.arangodb_client', new_callable=AsyncMock) as mock_client:
        yield mock_client

@pytest.mark.asyncio
async def test_kafka_producer_startup_shutdown(mock_kafka_manager, mock_arangodb_client):
    # Mock the arangodb_client as well, since startup_event calls both
    await startup_event()
    mock_kafka_manager.start_producer.assert_called_once()
    mock_kafka_manager.send_message.assert_called_once()
    mock_arangodb_client.connect.assert_called_once() # Ensure arangodb connect is called
    
    await shutdown_event()
    mock_kafka_manager.stop_producer.assert_called_once()
    mock_arangodb_client.disconnect.assert_called_once() # Ensure arangodb disconnect is called

@pytest.mark.asyncio
async def test_arangodb_client_startup_shutdown_isolated(mock_kafka_manager, mock_arangodb_client):
    # This test specifically focuses on arangodb client, ensuring kafka_manager is also mocked
    await startup_event()
    mock_arangodb_client.connect.assert_called_once()
    mock_kafka_manager.start_producer.assert_called_once() # Ensure kafka producer is called

    await shutdown_event()
    mock_arangodb_client.disconnect.assert_called_once()
    mock_kafka_manager.stop_producer.assert_called_once() # Ensure kafka producer is stopped

@pytest.mark.asyncio
async def test_get_candles_endpoint(mock_arangodb_client):
    mock_arangodb_client.fetch_candles.return_value = [{"_key": "1", "symbol": "BTCUSDT", "open": 100, "close": 110}]
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/candles/test_collection/BTCUSDT")
        assert response.status_code == 200
        assert response.json() == [{"_key": "1", "symbol": "BTCUSDT", "open": 100, "close": 110}]
        mock_arangodb_client.fetch_candles.assert_called_once_with("test_collection", "BTCUSDT", 100)

@pytest.mark.asyncio
async def test_get_candles_endpoint_not_found(mock_arangodb_client):
    mock_arangodb_client.fetch_candles.return_value = []
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/candles/test_collection/UNKNOWN")
        assert response.status_code == 404
        assert response.json() == {"detail": "Candles not found"}

@pytest.mark.asyncio
async def test_get_rsi_endpoint(mock_arangodb_client):
    mock_arangodb_client.fetch_rsi.return_value = [{"_key": "1", "symbol": "BTCUSDT", "value": 70}]
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/rsi/test_collection/BTCUSDT")
        assert response.status_code == 200
        assert response.json() == [{"_key": "1", "symbol": "BTCUSDT", "value": 70}]
        mock_arangodb_client.fetch_rsi.assert_called_once_with("test_collection", "BTCUSDT", 100)

@pytest.mark.asyncio
async def test_get_rsi_endpoint_not_found(mock_arangodb_client):
    mock_arangodb_client.fetch_rsi.return_value = []
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/rsi/test_collection/UNKNOWN")
        assert response.status_code == 404
        assert response.json() == {"detail": "RSI data not found"}
