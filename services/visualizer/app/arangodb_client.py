from aioarango import ArangoClient
from loguru import logger

from app.settings import settings

class ArangoDBClient:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        logger.info("Connecting to ArangoDB...")
        self.client = ArangoClient(hosts=settings.ARANGO_URL)
        self.db = await self.client.db(
            settings.ARANGO_DB,
            username=settings.ARANGO_USER,
            password=settings.ARANGO_PASSWORD,
        )
        logger.info("Connected to ArangoDB")

    async def disconnect(self):
        if self.client:
            logger.info("Disconnecting from ArangoDB")
            await self.client.close()
            logger.info("Disconnected from ArangoDB")

    async def fetch_candles(self, collection_name: str, symbol: str, limit: int = 100):
        if not self.db:
            logger.warning("ArangoDB not connected. Call connect() first.")
            return []
        
        query = f"FOR doc IN {collection_name} FILTER doc.symbol == @symbol SORT doc.timestamp DESC LIMIT @limit RETURN doc"
        cursor = await self.db.aql.execute(query, bind_vars={"symbol": symbol, "limit": limit})
        candles = [doc async for doc in cursor]
        logger.info(f"Fetched {len(candles)} candles from {collection_name} for {symbol}")
        return candles

    async def fetch_rsi(self, collection_name: str, symbol: str, limit: int = 100):
        if not self.db:
            logger.warning("ArangoDB not connected. Call connect() first.")
            return []
        
        query = f"FOR doc IN {collection_name} FILTER doc.symbol == @symbol SORT doc.timestamp DESC LIMIT @limit RETURN doc"
        cursor = await self.db.aql.execute(query, bind_vars={"symbol": symbol, "limit": limit})
        rsi_data = [doc async for doc in cursor]
        logger.info(f"Fetched {len(rsi_data)} RSI data points from {collection_name} for {symbol}")
        return rsi_data

arangodb_client = ArangoDBClient()
