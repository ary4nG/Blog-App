import json

from aiokafka import AIOKafkaProducer

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

TOPIC = "blog-events"

_producer: AIOKafkaProducer | None = None


async def start() -> None:
    """Create and connect the shared producer. Called once on app startup."""
    global _producer
    _producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
    await _producer.start()
    logger.info("kafka_producer_started", servers=settings.KAFKA_BOOTSTRAP_SERVERS)


async def stop() -> None:
    """Flush and close the producer. Called once on app shutdown."""
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None
        logger.info("kafka_producer_stopped")


async def publish(event: dict) -> None:
    """Publish an event to blog-events. FAIL-SAFE: never raises — if Kafka is
    down, we log a warning and return, so the API request still succeeds."""
    if _producer is None:
        logger.warning("kafka_publish_skipped", reason="producer_not_started")
        return
    try:
        # Kafka only takes bytes: dict -> JSON string -> bytes
        value = json.dumps(event).encode()
        # Key by post_id so all events for one post land in the same partition
        # (guaranteeing their order — see B.1). Both event types carry post_id.
        key = str(event["post_id"]).encode()
        await _producer.send_and_wait(TOPIC, value=value, key=key)
        logger.info("event_published", event_type=event.get("event"), post_id=event.get("post_id"))
    except Exception as e:
        # Swallow the error — publishing must never break the request.
        logger.warning("kafka_publish_failed", error=str(e), event_type=event.get("event"))
