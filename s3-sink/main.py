from quixstreams import Application
from iceberg_sink import IcebergSink
import os

from dotenv import load_dotenv
load_dotenv()

app = Application(consumer_group="destination-v2.17", 
                  auto_offset_reset = "earliest",
                  commit_interval=5)

input_topic = app.topic(os.environ["input"])

iceberg_sink = IcebergSink(
    os.environ["table_name"],
    os.environ["AWS_S3_URI"],
    s3_region_name=os.environ["AWS_DEFAULT_REGION"],)

sdf = app.dataframe(input_topic)
sdf.sink(iceberg_sink)

if __name__ == "__main__":
    app.run(sdf)