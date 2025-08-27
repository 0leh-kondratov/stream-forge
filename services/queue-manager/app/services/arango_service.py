from loguru import logger
from arango import ArangoClient
from app.config import settings # Use settings from config
from app.models.commands import QueueStartRequest
from app.models.telemetry import QueueTelemetry # Import QueueTelemetry

class ArangoQueueStore:
    def __init__(self):
        self.client = ArangoClient(hosts=settings.ARANGO_URL)
        self.db = None
        self.queues_collection = None # To store queue metadata
        self.telemetry_collection = None # To store telemetry events

    async def connect(self): # Make connect async
        try:
            sys_db = self.client.db("_system", username=settings.ARANGO_USER, password=settings.ARANGO_PASSWORD)
            if not await sys_db.has_database(settings.ARANGO_DB): # Await has_database
                await sys_db.create_database(settings.ARANGO_DB) # Await create_database
                logger.info(f"📁 Создана база данных: {settings.ARANGO_DB}")
            self.db = self.client.db(settings.ARANGO_DB, username=settings.ARANGO_USER, password=settings.ARANGO_PASSWORD)
            
            # Ensure collections exist
            if not await self.db.has_collection("queues"):
                self.queues_collection = await self.db.create_collection("queues")
                logger.info("📦 Создана коллекция: queues")
            else:
                self.queues_collection = self.db.collection("queues")

            if not await self.db.has_collection("telemetry_events"):
                self.telemetry_collection = await self.db.create_collection("telemetry_events")
                logger.info("📦 Создана коллекция: telemetry_events")
            else:
                self.telemetry_collection = self.db.collection("telemetry_events")

            logger.info(f"Connected to ArangoDB: {settings.ARANGO_DB}")
        except Exception as e:
            logger.error(f"Failed to connect to ArangoDB: {e}")
            raise

    async def save_queue_meta(self, queue_id: str, command: QueueStartRequest):
        """Saves initial metadata for a new queue/workflow."""
        if not self.queues_collection:
            await self.connect() # Ensure connected
        
        doc = command.model_dump() # Use model_dump for Pydantic v2
        doc["_key"] = queue_id
        doc["status"] = "pending" # Initial status
        doc["created_at"] = logger._time() # Use loguru's time for consistency
        
        await self.queues_collection.insert(doc)
        logger.info(f"Сохранение метаданных для очереди: {queue_id}")

    async def update_queue_status(self, queue_id: str, status: str, message: str = None):
        """Updates the status of a queue."""
        if not self.queues_collection:
            await self.connect()
        
        update_doc = {"status": status, "updated_at": logger._time()}
        if message:
            update_doc["message"] = message
        
        await self.queues_collection.update_match({"_key": queue_id}, update_doc)
        logger.info(f"Обновлен статус очереди {queue_id} на: {status}")

    async def list_all_queues(self):
        """Lists all queues."""
        if not self.queues_collection:
            await self.connect()
        
        cursor = self.queues_collection.aql.execute("FOR q IN queues RETURN q")
        queues = [doc async for doc in cursor] # Async comprehension
        return queues

    async def save_telemetry_event(self, telemetry_event: QueueTelemetry):
        """Saves a telemetry event."""
        if not self.telemetry_collection:
            await self.connect()
        
        doc = telemetry_event.model_dump()
        doc["_key"] = f"{telemetry_event.queue_id}-{telemetry_event.timestamp}-{telemetry_event.producer}" # Generate a unique key
        await self.telemetry_collection.insert(doc)
        logger.debug(f"Сохранено событие телеметрии для {telemetry_event.queue_id}")

# Instantiate the service
arango_service = ArangoQueueStore()