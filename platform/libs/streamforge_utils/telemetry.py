import asyncio
from aiokafka import AIOKafkaProducer

class TelemetryClient:
    def __init__(self, bootstrap_servers: str, topic: str):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
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

    async def send(self, message: dict):
        if not self.producer:
            raise RuntimeError("TelemetryClient is not connected. Call connect() first.")
        
        await self.producer.send_and_wait(self.topic, str(message).encode('utf-8'))
