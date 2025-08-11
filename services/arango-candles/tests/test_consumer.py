import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import pandas as pd
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# Import the function to be tested
from app.consumer import calculate_and_update_indicators

@pytest.fixture
def mock_arango_collection():
    """Pytest fixture to create a mock ArangoDB collection object."""
    mock_collection = MagicMock()
    mock_db = MagicMock()
    mock_aql = MagicMock()
    
    # Mock the AQL query execution
    mock_db.aql.execute = MagicMock()
    mock_collection.db = mock_db
    
    # Mock the update method
    mock_collection.update = MagicMock()
    
    return mock_collection

@pytest.mark.asyncio
async def test_calculate_and_update_indicators_success(mock_arango_collection):
    """Test that indicators are calculated and the document is updated successfully."""
    # 1. Prepare Test Data
    symbol = "BTCUSDT"
    latest_timestamp = 1672531200 # Example: 2023-01-01
    
    # Create a sample of historical candle data (as dicts)
    historical_data = []
    for i in range(50):
        historical_data.append({
            '_key': f'{symbol}-{latest_timestamp - (50 - i) * 60}',
            'symbol': symbol,
            'timestamp': latest_timestamp - (50 - i) * 60,
            'open': 16500 + i * 10,
            'high': 16550 + i * 10,
            'low': 16450 + i * 10,
            'close': 16520 + i * 10,
            'volume': 100 + i * 5
        })
    
    latest_doc = historical_data[-1]

    # Mock the return value of the AQL query to be in descending order like the real query
    mock_arango_collection.db.aql.execute.return_value = iter(historical_data[::-1])

    # 2. Call the function under test
    await calculate_and_update_indicators(mock_arango_collection, symbol, latest_timestamp)

    # 3. Assertions
    mock_arango_collection.db.aql.execute.assert_called_once()
    mock_arango_collection.update.assert_called_once()
    
    update_call_args = mock_arango_collection.update.call_args
    updated_key = update_call_args[0][0]
    updated_data = update_call_args[0][1]
    
    assert updated_key == latest_doc['_key']
    assert "EMA_50" in updated_data
    assert "RSI_14" in updated_data
    assert "VWAP_D" in updated_data

@pytest.mark.asyncio
async def test_no_historical_data(mock_arango_collection):
    """Test that the function handles cases with no historical data gracefully."""
    mock_arango_collection.db.aql.execute.return_value = iter([])

    await calculate_and_update_indicators(mock_arango_collection, "ETHUSDT", 1672531200)

    mock_arango_collection.update.assert_not_called()

@pytest.mark.asyncio
async def test_indicator_calculation_error(mock_arango_collection):
    """Test that an error during indicator calculation is handled gracefully."""
    bad_data = [{
        '_key': 'key1',
        'symbol': 'SOLUSDT',
        'timestamp': 12345
    }]
    mock_arango_collection.db.aql.execute.return_value = iter(bad_data)

    try:
        await calculate_and_update_indicators(mock_arango_collection, "SOLUSDT", 12345)
    except Exception as e:
        pytest.fail(f"Function raised an unexpected exception: {e}")

    mock_arango_collection.update.assert_not_called()
