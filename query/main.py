from quixstreams import Application, State
from iceberg_sink import IcebergSink
import os
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()
    
app = Application(consumer_group=os.environ["consumer_group"], 
                  auto_offset_reset = "earliest",
                  commit_interval=float(os.environ["commit_interval"]),
                  commit_every=int(os.environ["commit_every"]))


# We deserialize only messages with columns we need.
input_topic = app.topic(os.environ["input"], key_deserializer="string", value_deserializer="json")

iceberg_sink = IcebergSink(
    postgres_connection_str=os.environ["POSTGRES_CONNECTION_STR"],
    aws_s3_uri=os.environ["AZURE_STORAGE_URI"],
    namespace=os.environ["NAMESPACE"],
    table_name=os.environ["TABLE_NAME"],
    data_catalog_spec="postgres"
    )


sdf = app.dataframe(input_topic)




def aggregate_last_value(row: dict, state: State):
    
    last_values = state.get("last_values", {
        "type": None,
        "x": None,
        "y": None,
        "snakeLength": None,
        "session_id": None,
        "reason": None,
        "key": None
    })
    
    last_values = {
        **last_values,
        **row
    }
    
    state.set("last_values", last_values)
    
    return last_values
    
    

sdf = sdf.apply(aggregate_last_value, stateful=True)

sdf = sdf.apply(lambda row, key, timestamp, headers: {
    "_timestamp": datetime.fromtimestamp(timestamp/1000),
    "_key": key,
    **row
}, metadata=True)
sdf.print()
sdf.sink(iceberg_sink)

if __name__ == "__main__":
    app.run(sdf)