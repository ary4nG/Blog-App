"""Telemetry module for distributed tracing in FastAPI apps."""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from fastapi import FastAPI

from app.config.settings import settings
from .single_entry_trace_processor import AsyncElasticsearchTraceProcessor


class TelemetryManager:
    """A singleton class that handles telemetry initialization"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TelemetryManager, cls).__new__(cls)
        return cls._instance

    def initialize(self, app_name: str) -> None:
        """Initialize the telemetry configuration"""
        if self._initialized:
            return

        # Initialize tracer provider
        resource = Resource.create({"service.name": app_name})
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)

        processor = AsyncElasticsearchTraceProcessor(
            elasticsearch_url=settings.ELASTICSEARCH_URL,
            index_prefix=settings.ELASTIC_INDEX_PREFIX,
            username=settings.ELASTICSEARCH_USERNAME,
            password=settings.ELASTICSEARCH_PASSWORD,
            queue_size=10000,
            batch_size=100,
            export_timeout_secs=30,
        )
        tracer_provider.add_span_processor(processor)

        self._initialized = True


def setup_telemetry(app: FastAPI) -> None:
    """Set up telemetry for the FastAPI application"""
    # Initialize telemetry
    telemetry = TelemetryManager()
    telemetry.initialize(app.title)

    # Instrument the app
    FastAPIInstrumentor.instrument_app(app)
