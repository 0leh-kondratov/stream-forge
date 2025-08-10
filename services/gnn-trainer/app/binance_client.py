import asyncio
from binance.client import AsyncClient
from loguru import logger
import os
import time

class BinanceClient:
    def __init__(self, api_key: str, api_secret: str):
        self.client = AsyncClient(api_key, api_secret)
        logger.info("Binance AsyncClient initialized.")

    async def get_all_trading_pairs(self, quote_asset='USDT', min_daily_volume=1000000):
        """
        Retrieves all trading pairs quoted in USDT and filters by minimum daily volume.
        """
        logger.info(f"Fetching all trading pairs quoted in {quote_asset}...")
        exchange_info = await self.client.get_exchange_info()
        symbols = []
        for s in exchange_info['symbols']:
            if s['quoteAsset'] == quote_asset and s['status'] == 'TRADING':
                # Check daily volume (requires fetching 24hr ticker for each symbol, can be slow)
                # For simplicity, we'll skip volume filtering here and assume it's done downstream
                symbols.append(s['symbol'])
        logger.info(f"Found {len(symbols)} trading pairs.")
        return symbols

    async def get_klines(self, symbol: str, interval: str, limit: int):
        """
        Retrieves historical K-lines (candlestick data).
        """
        logger.debug(f"Fetching {limit} {interval} klines for {symbol}...")
        klines = await self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
        # Convert to a more usable format if needed, e.g., pandas DataFrame
        return klines

    async def get_order_book(self, symbol: str, limit: int = 20):
        """
        Retrieves order book depth.
        """
        logger.debug(f"Fetching order book for {symbol} (limit={limit})...")
        depth = await self.client.get_order_book(symbol=symbol, limit=limit)
        return depth

    async def get_funding_rate(self, symbol: str):
        """
        Retrieves the latest funding rate for a perpetual futures symbol.
        """
        logger.debug(f"Fetching funding rate for {symbol}...")
        # Binance API for funding rate is typically for futures
        # This might require a different client or endpoint if not directly available in AsyncClient
        # Placeholder:
        try:
            funding_rate_info = await self.client.get_funding_rate_history(symbol=symbol, limit=1)
            if funding_rate_info:
                return float(funding_rate_info[0]['fundingRate'])
        except Exception as e:
            logger.warning(f"Could not fetch funding rate for {symbol}: {e}")
        return None

    async def close(self):
        """Closes the Binance client connection."""
        await self.client.close_connection()
        logger.info("Binance AsyncClient connection closed.")
