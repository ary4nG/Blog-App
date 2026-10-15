"""
FastAPI application main entry point.

Initializes the application with authentication, logging, global exception handler, middleware,
and API route configurations.
"""

from fastapi import FastAPI, Depends
from itaap_python_utils.logging.manager import LogManager
from itaap_python_utils.exceptions.base import ServiceException
from app.middleware.trace_middleware import trace_middleware
from app.exceptions.handler import (
    handle_service_exception,
    handle_generic_exception,
)
from app.config.settings import settings
from app.dependencies.jwt_auth import TokenValidator
from app.routers import sample
from app.telemetry.config import setup_telemetry
import asyncio
from contextlib import asynccontextmanager
from app.events import consumer
from app.routers import activity

@asynccontextmanager
async def lifespan(app: FastAPI):
    await consumer.start()
    task = asyncio.create_task(consumer.consume_loop())
    yield 
    task.cancel()
    await consumer.stop()

app = FastAPI(title=settings.APP_NAME,lifespan=lifespan)

if settings.SEND_TELEMETRY_DATA.lower() == "true":
    setup_telemetry(app)

app.middleware("http")(trace_middleware)

app.add_exception_handler(ServiceException, handle_service_exception)
app.add_exception_handler(Exception, handle_generic_exception)

validator = TokenValidator()
app.include_router(sample.router, prefix=f"/{settings.APP_NAME}", dependencies=[Depends(validator)])
app.include_router(activity.router,prefix=f"/{settings.APP_NAME}")
# Initialize logger
LogManager.init_logger(
    app_name=settings.APP_NAME,
    app_version=settings.APP_VERSION,
    environment=settings.APP_ENV,
    log_level=settings.LOG_LEVEL_APP,
)

logger = LogManager.get_logger()


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting server")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9000,
        reload=True,
        access_log=True,
        log_level="error",
    )
