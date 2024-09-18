import os
from quixstreams import Application

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

app = Application(consumer_group="transformation-v1", auto_offset_reset="earliest")

input_topic = app.topic(os.environ["input"])
output_topic = app.topic(os.environ["output"])

sdf = app.dataframe(input_topic)

def should_skip(data):
    return data.get('type') == "apple-eaten"

sdf = (
    sdf.filter(should_skip)
    # Extract "temperature" value from the message
    .apply(lambda value: value["type"])
    # You can also pass duration_ms as an integer of milliseconds
    .tumbling_window(duration_ms=5000)
    # Specify the "mean" aggregate function
    .mean()
    # Emit updates for each incoming message
    .current()
)

sdf.print()
sdf.to_topic(output_topic)

if __name__ == "__main__":
    app.run(sdf)