import asyncio
import websockets
from websockets.exceptions import ConnectionClosedError
import os
from quixstreams import Application
from dotenv import load_dotenv
import uuid
import json
load_dotenv()






# from quixstreams import Application
# # Initialize the application
# app = Application(consumer_group='my-consumer-group')
# # Define the input topic
# input_topic = app.topic("score")
# # Create a consumer
# with app.get_consumer() as consumer:
#     # Subscribe to the topic
#     consumer.subscribe([input_topic.name])
#     while True:
#         msg = consumer.poll(timeout=1.0)
#         print(msg)
#         if msg is not None:
#             print(f'Received a message from topic {msg.topic()}: {msg.value()}')
#             # Optionally commit the offset
#             consumer.store_offsets(msg)





# def handle_consumer_error(e):
#     print(e)

# app = Application.Quix("web-sockets-server-v10000000", auto_offset_reset="earliest", loglevel='DEBUG',
# on_consumer_error=handle_consumer_error)
# topic = app.topic(name=os.environ["input"])
# consumer = app.get_consumer()

# print(topic.name)
# consumer.subscribe([topic.name])

# while True:
#     message = consumer.poll(1)
#     print(message)


class webSocketSource:
    
    def __init__(self) -> None:
        app = Application.Quix("web-sockets-server-v100", auto_offset_reset="latest", loglevel= 'DEBUG')
        self._topic = app.topic(name=os.environ["input"])
        
        self._consumer = app.get_consumer()
        self._consumer.subscribe([self._topic.name])
        # self._consumer.subscribe(["score"])

        # Holds all client connections partitioned by page.
        self.websocket_connections = {}
        
        # Instead of directly creating a task in the constructor, 
        # we'll start the task from outside to avoid issues with incomplete initialization.
        
    async def consume_messages(self):
        while True:
            message = self._consumer.poll(1)
            print(message)
            if message is not None:
                print(message.value())
                value = json.loads(bytes.decode(message.value()))
                key = bytes.decode(message.key())
                print(key)
                print(value)
                if key in self.websocket_connections:
                    for client in self.websocket_connections[key]:
                        try:
                            print(f"Sending: {value}")
                            await client.send(json.dumps(value))
                        except:
                            print("Connection already closed.")
                    
                    print(value)
                    print(f"Send to {key} {str(len(self.websocket_connections[key]))} times.")
            else:
                await asyncio.sleep(1)
                
            
    async def handle_websocket(self, websocket, path):
        print(f"Client connected to socket. Path={path}")
        
        if path not in self.websocket_connections:
            self.websocket_connections[path] = []

        self.websocket_connections[path].append(websocket)

        try:
            print("Keep the connection open and wait for messages if needed")
            await websocket.wait_closed()
        except websockets.exceptions.ConnectionClosedOK:
            print(f"Client {path} disconnected normally.")
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Client {path} disconnected with error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            print("Removing client from connection list")
            if path in self.websocket_connections:
                self.websocket_connections[path].remove(websocket)  # Use `del` to remove items from a dictionary

    async def start_websocket_server(self):
        print("listening for websocket connections..")
        server = await websockets.serve(self.handle_websocket, '0.0.0.0', 80)
        await server.wait_closed()

async def main():
    client = webSocketSource()
    # Start consuming messages as a separate task
    asyncio.create_task(client.consume_messages())
    await client.start_websocket_server()

# Run the application with exception handling
try:
    asyncio.run(main())
except Exception as e:
    print(f"An error occurred: {e}")
