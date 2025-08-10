import aiohttp
import asyncio
from loguru import logger
from datetime import datetime
from app import config

class BinanceAPIClient:
    BASE_URL = "https://api.binance.com/api/v3" # Spot API

    def __init__(self, api_key: str, api_secret: str):
        self.session = None
        self.api_key = api_key
        self.api_secret = api_secret
        logger.info("Binance API Client initialized.")

    async def _get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def get_historical_trades(self, symbol: str, start_time: int = None, end_time: int = None, limit: int = 1000):
        """
        Fetches historical trades from Binance.
        start_time and end_time should be Unix timestamps in milliseconds.
        """
        session = await self._get_session()
        params = {
            "symbol": symbol,
            "limit": limit,
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        url = f"{self.BASE_URL}/aggTrades" # Aggregated trades endpoint
        logger.debug(f"Fetching trades from {url} with params: {params}")
        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status() # Raise an exception for HTTP errors
                data = await response.json()
                logger.debug(f"Fetched {len(data)} trades for {symbol}.")
                return data
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching trades for {symbol}: {e}")
            return None

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Binance API Client session closed.")
