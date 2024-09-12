from quixstreams import Application
from s3_sink import S3Sink
import os

from dotenv import load_dotenv
load_dotenv()


app = Application(consumer_group="destination-v1.5", auto_offset_reset = "earliest")

input_topic = app.topic(os.environ["input"])
output_s3 = S3Sink(
    "quix-pc1hsusp59yhbmbszrpaz3epcjtp1eun1a-s3alias",
    "AKIA5JJJFC76E24MEO5M",
    "hkTwOVve8Fn901ra2nHvfl3Cssgqzh8pD3OF2TPm",
    format="parquet")

sdf = app.dataframe(input_topic)
# you can print the data row if you want to see what's going on.
sdf = sdf.update(lambda row: print(row))
# call the sink function for every message received.
sdf.sink(output_s3)

if __name__ == "__main__":
    app.run(sdf)