from quixstreams import Application
from s3_sink import S3Sink
import os

from dotenv import load_dotenv
load_dotenv()

# Load environment variables
s3_bucket_name = os.getenv('s3_bucket_name')
s3_access_key_id = os.getenv('s3_access_key_id')
s3_secret_access_key = os.getenv('s3_secret_access_key')
format = os.getenv('format')

app = Application(consumer_group="destination-v1.4", auto_offset_reset = "earliest")

input_topic = app.topic(os.environ["input"])
output_s3 = S3Sink(
    s3_bucket_name,
    s3_access_key_id,
    s3_secret_access_key,
    format=format)

sdf = app.dataframe(input_topic)
sdf = sdf.update(lambda row: print(row))

sdf.sink(output_s3)

if __name__ == "__main__":
    app.run(sdf)