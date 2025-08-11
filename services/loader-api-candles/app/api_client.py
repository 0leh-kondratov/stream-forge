import aiohttp
from loguru import logger
import asyncio

class BinanceAPIClient:
    BASE_URL = "https://api.binance.com/api/v3"

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret # Not directly used for public endpoints like klines
        self.session = None

    async def _get_session(self):
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def get_klines(self, symbol: str, interval: str, start_time: int = None, end_time: int = None, limit: int = 500):
        session = await self._get_session()
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        url = f"{self.BASE_URL}/klines"
        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status() # Raise an exception for bad status codes
                data = await response.json()
                return data
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None

    async def close(self):
        if self.session:
            await self.session.close()
            logger.info("BinanceAPIClient aiohttp session closed.")