import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import aiohttp

from app.api_client import BinanceAPIClient

@pytest.fixture
def mock_session():
    mock = AsyncMock(spec=aiohttp.ClientSession)
    mock.get.return_value.__aenter__.return_value = AsyncMock()
    return mock

@pytest.mark.asyncio
async def test_binance_api_client_get_klines_success(mock_session):
    mock_response = AsyncMock()
    mock_response.json.return_value = [["kline1"], ["kline2"]]
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value.__aenter__.return_value = mock_response

    with patch('aiohttp.ClientSession', return_value=mock_session):
        client = BinanceAPIClient("test_key", "test_secret")
        klines = await client.get_klines("BTCUSDT", "1h")

        assert klines == [["kline1"], ["kline2"]]
        mock_session.get.assert_called_once_with(
            "https://api.binance.com/api/v3/klines",
            params={'symbol': 'BTCUSDT', 'interval': '1h', 'limit': 500}
        )
        await client.close()

@pytest.mark.asyncio
async def test_binance_api_client_get_klines_http_error(mock_session):
    mock_response = AsyncMock()
    mock_response.raise_for_status.side_effect = aiohttp.ClientResponseError(request_info=None, history=(), status=400)
    mock_session.get.return_value.__aenter__.return_value = mock_response

    with patch('aiohttp.ClientSession', return_value=mock_session):
        client = BinanceAPIClient("test_key", "test_secret")
        klines = await client.get_klines("BTCUSDT", "1h")

        assert klines is None
        mock_session.get.assert_called_once()
        await client.close()

@pytest.mark.asyncio
async def test_binance_api_client_get_klines_network_error(mock_session):
    mock_session.get.side_effect = aiohttp.ClientConnectorError(connection_key=None, os_error=None)

    with patch('aiohttp.ClientSession', return_value=mock_session):
        client = BinanceAPIClient("test_key", "test_secret")
        klines = await client.get_klines("BTCUSDT", "1h")

        assert klines is None
        mock_session.get.assert_called_once()
        await client.close()

@pytest.mark.asyncio
async def test_binance_api_client_close_session():
    client = BinanceAPIClient("test_key", "test_secret")
    # Manually create a session to test closing
    client.session = AsyncMock(spec=aiohttp.ClientSession)
    client.session.closed = False

    await client.close()
    client.session.close.assert_called_once()
    assert client.session.closed
