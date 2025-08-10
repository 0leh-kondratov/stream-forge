# app/utils.py

import aiohttp
import asyncio
from datetime import datetime
from loguru import logger
from app.config import SYMBOL, TIME_RANGE, TYPE, INTERVAL, BINANCE_API_URL, BINANCE_WS_URL


def parse_time_range() -> tuple[int, int]:
    """
    Преобразует строку вида "2024-01-01:2024-01-02" в timestamps в миллисекундах.
    """
    start_str, end_str = TIME_RANGE.split(":")
    start = int(datetime.strptime(start_str, "%Y-%m-%d").timestamp() * 1000)
    end = int(datetime.strptime(end_str, "%Y-%m-%d").timestamp() * 1000)
    return start, end


async def fetch_api_candles(symbol: str, interval: str = "1m", limit: int = 1000):
    """
    Генератор свечей с Binance REST API.
    """
    start, end = parse_time_range()
    url = f"{BINANCE_API_URL}/api/v3/klines"

    async with aiohttp.ClientSession() as session:
        while start < end:
            params = {
                "symbol": symbol,
                "interval": interval,
                "startTime": start,
                "endTime": end,
                "limit": limit,
            }

            async with session.get(url, params=params) as response:
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(f"Ошибка Binance API: {response.status} - {text}")

                data = await response.json()

                if not data:
                    logger.info("⛔ Нет новых данных от Binance.")
                    break

                yield data
                last_timestamp = data[-1][0]
                start = last_timestamp + 60_000  # шаг в 1 минуту

            await asyncio.sleep(0.3)


async def fetch_ws_stream(symbol: str, stream_type: str = "kline", interval: str = "1m"):
    """
    Генератор данных с Binance WebSocket stream.
    stream_type может быть 'kline', 'trade', 'depth' и т.п.
    """
    stream = f"{symbol.lower()}@{stream_type}{interval}" if stream_type == "kline" else f"{symbol.lower()}@{stream_type}"
    url = f"{BINANCE_WS_URL}/{stream}"

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            logger.info(f"🔌 WebSocket подключение установлено: {url}")
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = msg.json()
                    yield [data]
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"Ошибка WebSocket: {msg.data}")
                    break


async def fetch_binance_data():
    """
    Унифицированная функция генерации данных с Binance по TYPE.
    Поддерживает: api_candles_1m, ws_candles_1m, ws_trades и др.
    """
    if TYPE.startswith("api_candles"):
        interval = TYPE.split("_")[-1]
        async for chunk in fetch_api_candles(SYMBOL, interval):
            yield chunk

    elif TYPE.startswith("ws_candles"):
        interval = TYPE.split("_")[-1]
        async for chunk in fetch_ws_stream(SYMBOL, stream_type="kline", interval=interval):
            yield chunk

    elif TYPE == "ws_trades":
        async for chunk in fetch_ws_stream(SYMBOL, stream_type="trade"):
            yield chunk

    else:
        raise ValueError(f"Неподдерживаемый TYPE: {TYPE}")
