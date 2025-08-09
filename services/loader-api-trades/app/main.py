# services/loader-api-trades/app/main.py

import asyncio
from loguru import logger

async def main():
    logger.info("Loader API Trades service started.")
    # Здесь будет логика загрузки данных по сделкам
    while True:
        await asyncio.sleep(3600) # Keep service alive


if __name__ == "__main__":
    asyncio.run(main())
