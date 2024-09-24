from quixstreams import Application
from s3_sink import S3Sink
import os

from dotenv import load_dotenv
load_dotenv()

app = Application(consumer_group="destination-v2.17", 
                  auto_offset_reset = "earliest",
                  commit_interval=5)

input_topic = app.topic(os.environ["input"])

output_s3 = S3Sink(
    os.environ["AWS_S3_URI"],
    os.environ["table_name"],
    s3_region_name=os.environ["AWS_DEFAULT_REGION"],)

sdf = app.dataframe(input_topic)
sdf.sink(output_s3)

if __name__ == "__main__":
    app.run(sdf)