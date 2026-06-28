from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.database import engine, Base
from app.routers import (
    import_router,
    query_router,
    risk_router,
    enrich_router,
    report_router,
)
import logging
from app.config import settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logging.getLogger("langchain_google_genai._function_utils").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Initializing DarkAtlas API startup sequence...")
    try:
        # Verify connection
        with engine.connect() as conn:
            logger.info(
                f"Successfully connected to database at {settings.DATABASE_URL.split('@')[-1]}"
            )
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
        raise e

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified.")

    yield

    # Shutdown logic
    logger.info("Shutting down DarkAtlas API...")
    engine.dispose()
    logger.info("Database connections closed.")


from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(
    title="DarkAtlas Asset Management System API",
    description="FastAPI + PostgreSQL foundation for an ASM platform with LangChain analysis layer",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(import_router.router)
app.include_router(query_router.router)
app.include_router(risk_router.router)
app.include_router(enrich_router.router)
app.include_router(report_router.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the DarkAtlas Asset Management System API"}
