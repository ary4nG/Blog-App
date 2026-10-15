import aiokafka
from aiokafka import AIOKafkaConsumer
import json
import logging
from app.config.settings import settings
from collections import deque

logger = logging.getLogger(__name__)

_activity: deque = deque(maxlen=100)

# hold a placeholder now; the REAL consumer is built inside start() (when the
# event loop is running). Building an aiokafka client at import time crashes.
_consumer: AIOKafkaConsumer | None = None

async def start()->None:
    global _consumer
    _consumer = AIOKafkaConsumer(
        "blog-events",
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="activity-service",
    )
    await _consumer.start()
    logger.warning("kafka_consumer_started")

async def stop()->None:
    global _consumer
    if _consumer is not None:
        await _consumer.stop()
        _consumer = None
        logger.warning("kafka_consumer_stopped")

async def consume_loop()->None:
    async for msg in _consumer:
        try:
            event = json.loads(msg.value)
            _activity.append(event)
            logger.warning(
                "event_consumed event=%s partition=%s offset=%s",
                event.get("event"), msg.partition, msg.offset,
            )
        except Exception as e:
            logger.warning("bad_message error=%s", str(e))

