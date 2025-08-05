from loguru import logger
from aioarango import ArangoClient
from aioarango.database import StandardDatabase
from aioarango.exceptions import ArangoServerError
from app.config import ARANGO_URL, ARANGO_DB, ARANGO_USER, ARANGO_PASSWORD


class AsyncArangoConnector:
    def __init__(self):
        self.client = ArangoClient()
        self.db: StandardDatabase | None = None

    async def connect(self):
        try:
            conn = await self.client.connect(
                ARANGO_URL,
                username=ARANGO_USER,
                password: "REDACTED",
            )
            self.db = await conn.db(ARANGO_DB)
            logger.info("✅ Подключено к ArangoDB.")
        except ArangoServerError as e:
            logger.error(f"❌ Ошибка подключения к ArangoDB: {e}")
            raise

    async def ensure_collection(self, name: str):
        assert self.db
        if not await self.db.has_collection(name):
            await self.db.create_collection(name)
            logger.info(f"📁 Коллекция создана: {name}")
        return await self.db.collection(name)

    async def insert_documents(self, collection_name: str, docs: list[dict]):
        try:
            collection = await self.ensure_collection(collection_name)
            await collection.insert_many(docs)
            logger.debug(f"📥 Вставлено документов: {len(docs)}")
        except Exception as e:
            logger.error(f"❌ Ошибка вставки в ArangoDB: {e}")

    async def close(self):
        await self.client.close()
        logger.info("🔌 Соединение с ArangoDB закрыто.")
