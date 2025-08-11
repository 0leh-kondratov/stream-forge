from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from prometheus_client import generate_latest, Counter, Gauge
from loguru import logger
import asyncio
import time
from unittest.mock import AsyncMock # Import AsyncMock
from pathlib import Path # Import Path

from app.settings import settings
from app.kafka_consumer import kafka_manager as real_kafka_manager
from app.arangodb_client import arangodb_client as real_arangodb_client

# Conditionally use real or mocked clients
if settings.TESTING:
    logger.info("Running in TESTING mode: Mocking Kafka and ArangoDB clients.")
    kafka_manager = AsyncMock()
    arangodb_client = AsyncMock()
else:
    kafka_manager = real_kafka_manager
    arangodb_client = real_arangodb_client

app = FastAPI()

# Correctly set the templates directory relative to the current file
templates = Jinja2Templates(directory=Path(__file__).parent / "frontend")

# Prometheus Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint'])
REQUEST_DURATION = Gauge('http_request_duration_seconds', 'HTTP Request Duration', ['method', 'endpoint'])
WEBSOCKET_CONNECTIONS = Gauge('websocket_connections', 'Number of active WebSocket connections')

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up application...")
    await kafka_manager.start_producer()
    await arangodb_client.connect()
    # Send a startup telemetry message
    await kafka_manager.send_message(
        settings.QUEUE_EVENTS_TOPIC,
        {
            "queue_id": settings.QUEUE_ID,
            "telemetry_id": settings.TELEMETRY_PRODUCER_ID,
            "status": "started",
            "message": "Visualizer application started",
            "timestamp": time.time(),
            "producer": settings.TELEMETRY_PRODUCER_ID,
            "finished": False
        }
    )

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")
    # Send a shutdown telemetry message
    await kafka_manager.send_message(
        settings.QUEUE_EVENTS_TOPIC,
        {
            "queue_id": settings.QUEUE_ID,
            "telemetry_id": settings.TELEMETRY_PRODUCER_ID,
            "status": "finished",
            "message": "Visualizer application shut down",
            "timestamp": time.time(),
            "producer": settings.TELEMETRY_PRODUCER_ID,
            "finished": True
        }
    )
    await kafka_manager.stop_producer()
    await arangodb_client.disconnect()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    response = await call_next(request)
    return response

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/metrics")
async def metrics():
    return HTMLResponse(content=generate_latest().decode("utf-8"), media_type="text/plain")

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/candles/{collection_name}/{symbol}") # Reverted endpoint
async def get_candles(collection_name: str, symbol: str, limit: int = 100):
    logger.info(f"Received request for candles: {collection_name}, {symbol}")
    candles = await arangodb_client.fetch_candles(collection_name, symbol, limit)
    logger.info(f"Fetched candles: {len(candles)}")
    if not candles:
        raise HTTPException(status_code=404, detail="Candles not found")
    return candles

@app.get("/rsi/{collection_name}/{symbol}") # Reverted endpoint
async def get_rsi(collection_name: str, symbol: str, limit: int = 100):
    logger.info(f"Received request for RSI: {collection_name}, {symbol}")
    rsi_data = await arangodb_client.fetch_rsi(collection_name, symbol, limit)
    logger.info(f"Fetched RSI data: {len(rsi_data)}")
    if not rsi_data:
        raise HTTPException(status_code=404, detail="RSI data not found")
    return rsi_data

@app.websocket("/ws/topic/{kafka_topic}")
async def websocket_endpoint(websocket: WebSocket, kafka_topic: str):
    await websocket.accept()
    WEBSOCKET_CONNECTIONS.inc()
    logger.info(f"WebSocket connected to topic: {kafka_topic}")
    
    # Start Kafka consumer for this specific topic
    await kafka_manager.start_consumer(kafka_topic)

    try:
        if settings.TESTING: # Simplified behavior for testing
            while True:
                await asyncio.sleep(1) # Keep connection alive, but don't consume
        else:
            async for message in kafka_manager.consume_messages():
                await websocket.send_json(message)
    except WebSocketDisconnect:
        WEBSOCKET_CONNECTIONS.dec()
        logger.info(f"WebSocket disconnected from topic: {kafka_topic}")
    except Exception as e:
        WEBSOCKET_CONNECTIONS.dec()
        logger.error(f"WebSocket error: {e}")
    finally:
        # Stop Kafka consumer when WebSocket disconnects
        await kafka_manager.stop_consumer()