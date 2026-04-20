import json
from typing import Any

from aiokafka import AIOKafkaProducer
from loguru import logger

from setting import kafka_config


class KafkaProvider:
    _producer: AIOKafkaProducer | None = None

    @classmethod
    async def init_producer(cls) -> None:
        """Initialize Kafka producer for the application lifecycle."""
        if not kafka_config.enabled:
            logger.debug("Kafka integration is disabled")
            return

        if cls._producer is not None:
            return

        logger.debug(
            f"Starting Kafka producer: bootstrap_servers={kafka_config.bootstrap_servers}, "
            f"client_id={kafka_config.client_id}"
        )
        cls._producer = AIOKafkaProducer(
            bootstrap_servers=kafka_config.bootstrap_servers_list,
            client_id=kafka_config.client_id,
            key_serializer=cls._serialize_key,
            value_serializer=cls._serialize_value,
        )
        await cls._producer.start()
        logger.info("Kafka producer started")

    @classmethod
    async def dispose_producer(cls) -> None:
        """Close Kafka producer on application shutdown."""
        if cls._producer is not None:
            await cls._producer.stop()
            cls._producer = None
            logger.info("Kafka producer stopped")

    @classmethod
    async def publish(
        cls,
        topic: str,
        value: dict[str, Any],
        key: str | None = None,
        headers: list[tuple[str, bytes]] | None = None,
    ) -> None:
        """Publish one JSON event to Kafka."""
        if not kafka_config.enabled:
            raise RuntimeError("Kafka integration is disabled")

        if cls._producer is None:
            await cls.init_producer()

        if cls._producer is None:
            raise RuntimeError("Kafka producer is not initialized")

        await cls._producer.send_and_wait(
            topic=topic,
            value=value,
            key=key,
            headers=headers,
        )

    @staticmethod
    def _serialize_key(value: str | None) -> bytes | None:
        if value is None:
            return None
        return value.encode("utf-8")

    @staticmethod
    def _serialize_value(value: dict[str, Any]) -> bytes:
        return json.dumps(value, ensure_ascii=False).encode("utf-8")
