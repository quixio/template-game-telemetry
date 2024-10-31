from quixstreams import Application, State
from iceberg_sink import IcebergSink
import os
from datetime import datetime

from pyiceberg.transforms import DayTransform, IdentityTransform
from pyiceberg.catalog.glue import GlueCatalog
from pyiceberg.catalog.sql import SqlCatalog
from pyiceberg.partitioning import PartitionSpec, PartitionField
from pyiceberg.schema import Schema, NestedField
from pyiceberg.types import StringType, TimestampType, IntegerType, LongType


from dotenv import load_dotenv
load_dotenv()
    
app = Application(consumer_group=os.environ["consumer_group"], 
                  auto_offset_reset = "earliest",
                  commit_interval=float(os.environ["commit_interval"]),
                  commit_every=int(os.environ["commit_every"]))


# We deserialize only messages with columns we need.
input_topic = app.topic(os.environ["input"], key_deserializer="string", value_deserializer="json")


# Define a default schema if none is provided.
schema = Schema(
    NestedField(1, "_timestamp", TimestampType(), required=False),
    NestedField(2, "_key", StringType(), required=False),
    NestedField(2, "type", StringType(), required=False),
    NestedField(2, "x", LongType(), required=False),
    NestedField(2, "y", LongType(), required=False),
    NestedField(2, "snakeLength", LongType(), required=False),
    NestedField(2, "session_id", StringType(), required=False),
    NestedField(2, "reason", StringType(), required=False),
    NestedField(2, "key", LongType(), required=False)
)

iceberg_sink = IcebergSink(
    postgres_connection_str=os.environ["POSTGRES_CONNECTION_STR"],
    aws_s3_uri=os.environ["AZURE_STORAGE_URI"],
    namespace=os.environ["NAMESPACE"],
    table_name=os.environ["TABLE_NAME"],
    data_catalog_spec="postgres",
    #schema=schema
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

sdf.sink(iceberg_sink)

if __name__ == "__main__":
    app.run(sdf)