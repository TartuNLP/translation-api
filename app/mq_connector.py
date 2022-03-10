import logging
import asyncio
import json

from pydantic import BaseModel
from aio_pika import ExchangeType, Message, IncomingMessage, connect_robust

from app import mq_settings

LOGGER = logging.getLogger(__name__)


class MQConnector:
    def __init__(self):
        self.futures = {}
        self.loop = asyncio.get_running_loop()

        self.connection = None
        self.channel = None
        self.exchange = None
        self.callback_queue = None

    async def connect(self):
        self.connection = await connect_robust(
            host=mq_settings.host,
            port=mq_settings.port,
            login=mq_settings.username,
            password=mq_settings.password,
            client_properties={
                'connection_name': mq_settings.connection_name
            }
        )
        self.channel = await self.connection.channel()
        self.exchange = await self.channel.declare_exchange(mq_settings.exchange, ExchangeType.DIRECT)
        self.callback_queue = await self.channel.declare_queue(exclusive=True)

        await self.callback_queue.consume(self.on_response)

    async def disconnect(self):
        await self.callback_queue.delete()
        await self.connection.close()

    def on_response(self, message: IncomingMessage):
        LOGGER.info(f"Received response for request: {{id: {message.correlation_id}}}")

        future = self.futures.pop(message.correlation_id)
        message.ack()
        future.set_result(json.loads(message.body))
        LOGGER.debug(f"Response for {message.correlation_id}: {json.loads(message.body)}")

    async def publish_request(self, correlation_id: str, body: BaseModel, routing_key: str):
        """
        Publishes the request to RabbitMQ.
        """
        future = self.loop.create_future()
        self.futures[correlation_id] = future

        body = body.json().encode()
        message = Message(
            body,
            content_type='application/json',
            correlation_id=correlation_id,
            expiration=mq_settings.timeout,
            reply_to=self.callback_queue.name
        )

        try:
            await self.exchange.publish(message, routing_key=routing_key)
        except Exception as e:
            LOGGER.exception(e)
            LOGGER.info("Attempting to restore the channel.")
            await self.channel.reopen()
            await self.exchange.publish(message, routing_key=routing_key)

        LOGGER.info(f"Sent request: {{id: {correlation_id}, routing_key: {routing_key}}}")
        LOGGER.debug(f"Request {correlation_id} content: {{id: {correlation_id}}}")
        response = await future  # TODO handle timeouts

        return response


mq_connector = MQConnector()
