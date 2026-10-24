import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api.routes_health import router as health_router
from .api.routes_analysis import router as analysis_router
from .api.routes_forecasts import router as forecasts_router
from .api.routes_quality import router as quality_router
from .services.data_pipeline import pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("windscope")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting WindScope application...")
    try:
        pipeline.initialize_data()
        logger.info("WindScope data pipeline successfully initialized on startup.")
    except Exception as e:
        logger.error(f"Failed to pre-warm data pipeline during startup: {e}. Will attempt on first request.")
    yield
    logger.info("Shutting down WindScope application...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="UK Wind Generation Forecast Analysis Platform using Official Elexon BMRS Data.",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api
app.include_router(health_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(forecasts_router, prefix="/api")
app.include_router(quality_router, prefix="/api")

@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/api/health",
        "analysis_url": "/api/analysis",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
