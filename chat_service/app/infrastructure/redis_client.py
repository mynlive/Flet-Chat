# app/infrastructure/redis_client.py
import redis.asyncio as redis
import logging

class RedisClient:
    def __init__(self, host: str, port: int, logger: logging.Logger):
        self.host = host
        self.port = port
        self.client = None
        self.logger = logger

    async def connect(self):
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            db=0,
            decode_responses=True,
        )
        try:
            await self.client.ping()
            self.logger.info(f"Successfully connected to Redis at {self.host}:{self.port}")
        except redis.ConnectionError as e:
            self.logger.error(f"Failed to connect to Redis: {str(e)}")
            self.logger.error(f"Redis host: {self.host}, Redis port: {self.port}")
            raise e

    async def disconnect(self):
        if self.client:
            await self.client.close()
            self.logger.info("Disconnected from Redis")

    async def publish(self, channel: str, message: str):
        await self.client.publish(channel, message)
        self.logger.debug(f"Published message to channel {channel}")