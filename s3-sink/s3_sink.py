import logging
from quixstreams.sinks import SinkBatch, BatchingSink
from formats import ParquetFormat

import logging
from typing import Literal, Optional

logger = logging.getLogger("quixstreams")

import pyarrow as pa
import pyarrow.parquet as pq

from pyiceberg.transforms import DayTransform, IdentityTransform
from pyiceberg.catalog.glue import GlueCatalog
from pyiceberg.partitioning import PartitionSpec, PartitionField
from pyiceberg.schema import Schema, NestedField
from pyiceberg.types import (
    StringType,
    TimestampType,
)


DataCatalogSpec = Literal["aws_glue"]

LogLevel = Literal[
    "CRITICAL",
    "ERROR",
    "WARNING",
    "INFO",
    "DEBUG",
    "NOTSET",
]


class S3Sink(BatchingSink):
    def __init__(
        self,
        aws_s3_uri: str,
        table_name: str,
        prefix: str = "",
        s3_region_name: Optional[str] = None,
        loglevel: LogLevel = "INFO"
    ):
        super().__init__()

        # Configure logging.
        self._logger = logging.getLogger("AwsKinesisSink")
        log_format = '[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(name)s] : %(message)s'
        logging.basicConfig(format=log_format, datefmt='%Y-%m-%d %H:%M:%S')
        self._logger.setLevel(loglevel)


        self._format = ParquetFormat()
        self._prefix = prefix
        
        # Configure Iceberg Catalog
        self.catalog = GlueCatalog(
            name="glue_catalog",
            region_name=s3_region_name
        )
        
        schema = Schema(
            NestedField(1, "_timestamp", TimestampType(), required=False),
            NestedField(2, "_key", StringType(), required=False)
        )
        
        # Create partition fields
        partition_fields = [
            PartitionField(
                source_id=2,
                field_id=1003,
                transform=IdentityTransform(),
                name='_key'
            ),
            PartitionField(
                source_id=1,
                field_id=1002,
                transform=DayTransform(),
                name='day'
            )
        ]

        # Create the new PartitionSpec
        new_partition_spec = PartitionSpec(schema=schema, fields=partition_fields)
        
        self.table = self.catalog.create_table_if_not_exists(table_name, schema, aws_s3_uri, partition_spec=new_partition_spec)
            
        # Define the new partition strategy (combining year from a timestamp and a string column)
        schema = self.table.schema()

        # Replace the existing partition spec with the new one
        self.table.update_spec(new_partition_spec)

        self._logger.info("Partition strategy successfully altered.")
        
  
        
    

    def write(self, batch: SinkBatch):
        
        data = self._format.serialize_batch_values(batch)
        
        input_buffer = pa.BufferReader(data)
        parquet_table = pq.read_table(input_buffer)
        
        # Apply the new schema to the table (if necessary)
        with self.table.update_schema() as update:
            update.union_by_name(parquet_table.schema)
            
        self.table.append(parquet_table)
        self._logger.info(f"Appended {len(list(batch))} records to {self.table.name()} table.")
        
    