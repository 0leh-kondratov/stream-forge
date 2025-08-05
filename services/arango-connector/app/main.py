# services/arango-connector/app/main.py

import asyncio
from loguru import logger

async def main():
    logger.info("Arango Connector service started.")
    # Здесь будет логика коннектора к ArangoDB
    while True:
        await asyncio.sleep(3600) # Keep service alive

if __name__ == "__main__":
    asyncio.run(main())
