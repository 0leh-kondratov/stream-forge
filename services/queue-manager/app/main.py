# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.logging_config import logger
from app.routes.queues import router as queue_router
from app.routes.health import router as health_router
from app.metrics.prometheus_metrics import setup_metrics

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Queue Manager started")
    yield
    # Shutdown
    logger.info("🛑 Queue Manager shutting down")

app = FastAPI(
    title="StreamForge Queue Manager",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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

# Metrics
setup_metrics(app)

# Routers
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(queue_router, prefix="/queues", tags=["queues"])
