import asyncio
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

class BaseProducer:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

    async def connect(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            loop=asyncio.get_event_loop()
        )
        await self.producer.start()

    async def disconnect(self):
        if self.producer:
            await self.producer.stop()

    async def send(self, topic: str, message: bytes):
        if not self.producer:
            raise RuntimeError("Producer is not connected. Call connect() first.")
        
        await self.producer.send_and_wait(topic, message)

class BaseConsumer:
    def __init__(self, bootstrap_servers: str, topic: str, group_id: str):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.consumer = None

    async def connect(self):
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            loop=asyncio.get_event_loop()
        )
        await self.consumer.start()

    async def disconnect(self):
        if self.consumer:
            await self.consumer.stop()

    async def consume(self):
        if not self.consumer:
            raise RuntimeError("Consumer is not connected. Call connect() first.")
        
        async for message in self.consumer:
            yield message
