import os
from quixstreams import Application
from xml_serializer import XMLSerializer, XM
# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

app = Application(consumer_group="xml-v1", auto_offset_reset="earliest")

input_topic = app.topic(os.environ["output"], value_deserializer=X)
#output_topic = app.topic(os.environ["output"], value_serializer=XMLSerializer())

sdf = app.dataframe(input_topic)


sdf.print()
sdf.to_topic(output_topic)

if __name__ == "__main__":
    app.run(sdf)