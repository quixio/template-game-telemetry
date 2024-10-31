import logging
from quixstreams.sinks import SinkBatch, BatchingSink
from formats import ParquetFormat
from typing import Literal, Optional
import pyarrow as pa
import pyarrow.parquet as pq
from pyiceberg.transforms import DayTransform, IdentityTransform
from pyiceberg.catalog.glue import GlueCatalog
from pyiceberg.catalog.sql import SqlCatalog
from pyiceberg.partitioning import PartitionSpec, PartitionField
from pyiceberg.schema import Schema, NestedField
from pyiceberg.types import StringType, TimestampType

DataCatalogSpec = Literal["aws_glue"]
LogLevel = Literal[
    "CRITICAL",
    "ERROR",
    "WARNING",
    "INFO",
    "DEBUG",
    "NOTSET",
]


class IcebergSink(BatchingSink):
    """
    IcebergSink is a sink that writes batches of data to an Apache Iceberg table stored in AWS S3,
    using the AWS Glue Data Catalog as a default catalog (only implemented for now).
    It serializes incoming data batches into Parquet format and appends them to the Iceberg table,
    updating the table schema as necessary on fly.
    """

    def __init__(
        self,
        namespace: str,
        table_name: str,
        postgres_connection_str: Optional[str] = None,
        aws_s3_uri: Optional[str] = None,
        s3_region_name: Optional[str] = None,
        data_catalog_spec: DataCatalogSpec = "aws_glue",
        schema: Optional[Schema] = None,
        partition_spec: Optional[PartitionSpec] = None,
        format=ParquetFormat(),
        loglevel: LogLevel = "INFO",
    ):
        """
        Initializes the S3Sink with the specified configuration.
        Parameters:
            table_name (str): The name of the Iceberg table.
            aws_s3_uri (str): The S3 URI where the table data will be stored (e.g., 's3://your-bucket/warehouse/').
            s3_region_name (Optional[str]): The AWS region where the S3 bucket and Glue catalog are located.
            data_catalog_spec (DataCatalogSpec): The data catalog specification to use (default is 'aws_glue').
            schema (Optional[Schema]): The Iceberg table schema. If None, a default schema is used.
            partition_spec (Optional[PartitionSpec]): The partition specification for the table. If None, a default is used.
            format: The data serialization format to use (default is ParquetFormat()).
            loglevel (LogLevel): The logging level for the logger (default is 'INFO').
        """
        super().__init__()

        # Configure logging.
        self._logger = logging.getLogger("IcebergSink")
        log_format = (
            "[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(name)s] : %(message)s"
        )
        logging.basicConfig(format=log_format, datefmt="%Y-%m-%d %H:%M:%S")
        self._logger.setLevel(loglevel)
        self._format = format

        # Initialize the Iceberg catalog.
        if data_catalog_spec == "aws_glue":
            # Configure Iceberg Catalog using AWS Glue.
            self.catalog = GlueCatalog(name="glue_catalog", region_name=s3_region_name)
        if data_catalog_spec == "postgres":
            # Load Iceberg catalog (assuming using Azure as storage)
            self.catalog = SqlCatalog("sql", uri=postgres_connection_str)
        else:
            raise ValueError(f"Unsupported data_catalog_spec: {data_catalog_spec}")

        try:
            print(namespace)
            print(self.catalog.list_namespaces())
            if namespace not in self.catalog.list_namespaces():
                print(f"Namespace {namespace} does not exist. Creating it...")
                self.catalog.create_namespace(namespace)
                print(f"Namespace {namespace} created successfully.")
            else:
                print(f"Namespace {namespace} already exists.")
        except Exception as e:
            print(f"Error while checking/creating namespace: {e}")

        # Set up the schema.
        if schema is None:
            # Define a default schema if none is provided.
            schema = Schema(
                NestedField(1, "_timestamp", TimestampType(), required=False),
                NestedField(2, "_key", StringType(), required=False),
            )

        # Set up the partition specification.
        if partition_spec is None:
            # Map field names to field IDs from the schema.
            field_ids = {field.name: field.field_id for field in schema.fields}
            # Create partition fields.
            partition_fields = [
                PartitionField(
                    source_id=field_ids["_key"],
                    field_id=1000,  # Unique partition field ID.
                    transform=IdentityTransform(),
                    name="_key",
                ),
                PartitionField(
                    source_id=field_ids["_timestamp"],
                    field_id=1001,
                    transform=DayTransform(),
                    name="day",
                ),
            ]
            # Create the new PartitionSpec.
            partition_spec = PartitionSpec(schema=schema, fields=partition_fields)

        # Create the Iceberg table if it doesn't exist.
        self.table = self.catalog.create_table_if_not_exists(
            identifier=f"{namespace}.{table_name}",
            schema=schema,
            location=aws_s3_uri,
            partition_spec=partition_spec,
        )
        self._logger.info(
            f"Loaded Iceberg table '{namespace}.{table_name}' at '{aws_s3_uri}'."
        )

    def write(self, batch: SinkBatch):
        """
        Writes a batch of data to the Iceberg table.
        Parameters:
            batch (SinkBatch): The batch of data to write.
        """
        try:
            # Serialize batch data into Parquet format.
            data = self._format.serialize_batch_values(batch)

            # Read data into a PyArrow Table.
            input_buffer = pa.BufferReader(data)
            parquet_table = pq.read_table(input_buffer)

            # Get the current schema of the Iceberg table.
            iceberg_schema = self.table.schema()

            # Convert the Iceberg schema to a PyArrow schema for comparison.
            iceberg_arrow_schema = iceberg_schema.as_arrow()

            # Get the incoming schema from the Parquet table.
            incoming_schema = parquet_table.schema

            schema_needs_update = False
            for field in incoming_schema:
                if iceberg_arrow_schema.get_field_index(field.name) == -1:
                    self._logger.info(f"{field.name} is missing in schema.")
                    schema_needs_update = True

            # If any field is missing, update the schema.
            if schema_needs_update:
                with self.table.update_schema() as update:
                    update.union_by_name(parquet_table.schema)
                    self._logger.info(f"Schema updated.")


            # Append the data to the table (this line is commented in the original, so adjust as needed).
            self.table.append(parquet_table)
            
            self._logger.info(
                f"Appended {len(list(batch))} records to table '{self.table.name()}'."
            )
        except Exception as e:
            self._logger.error(f"Error writing data to Iceberg table: {e}")
            raise
