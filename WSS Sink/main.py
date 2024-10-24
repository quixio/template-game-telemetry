import asyncio
import websockets
import os
from quixstreams import Application
from dotenv import load_dotenv
import json

class websocket_server:

    def __init__(self) -> None:
        app = Application("consumer-group", auto_offset_reset="latest")
        self._topic = app.topic(name=os.environ["input"])

        self._consumer = app.get_consumer()
        self._consumer.subscribe([self._topic.name])

    async def consume_messages(self):
        while True:
            message = self._consumer.poll(1)
            if message is not None:
                print(message.value())

    async def handle_websocket(self, websocket, path):
        ...

    async def start_websocket_server(self):
        ...

async def main():
    client = websocket_server()
    asyncio.create_task(client.consume_messages())

try:
    asyncio.run(main())
except Exception as e:
    print(f"An error has occurred: {e}")
