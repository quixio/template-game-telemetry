import os
from quixstreams import Application

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

app = Application(consumer_group="transformation-v1", auto_offset_reset="earliest")

input_topic = app.topic(os.environ["input"])
output_topic = app.topic(os.environ["output"])

sdf = app.dataframe(input_topic)

# In this case there is nothing to normalize
# However if you needed to you could write any code here to
# modify the incoming game data to suit your cheater detection model
# or other downstream services.

# see docs for what you can do
# https://quix.io/docs/get-started/quixtour/process-threshold.html

sdf.print()
sdf.to_topic(output_topic)

if __name__ == "__main__":
    app.run(sdf)