# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.logging_config import logger
from app.routes.queues import router as queue_router
from app.routes.health import router as health_router
from app.metrics.prometheus_metrics import setup_metrics

app = FastAPI(
    title="StreamForge Queue Manager",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Hosts
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Метрики
setup_metrics(app)

# Роутеры
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(queue_router, prefix="/queues", tags=["queues"])

# Логирование событий запуска
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Queue Manager запущен")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Queue Manager завершает работу")
