import abc
from gzip import compress as gzip_compress
from io import BytesIO
from typing import Any, List
from quixstreams.sinks.base import SinkBatch

from datetime import datetime

__all__ = ("S3SinkBatchFormat", "ParquetFormat")


class S3SinkBatchFormat:
    """
    Base class to format batches for S3 Sink
    """

    @property
    @abc.abstractmethod
    def file_extension(self) -> str:
        ...

    @abc.abstractmethod
    def deserialize_value(self, value: bytes) -> Any:
        ...

    @abc.abstractmethod
    def serialize_batch_values(self, values: List[Any]) -> List[bytes]:
        ...


import pyarrow as pa
import pyarrow.parquet as pq
import gzip

class ParquetFormat(S3SinkBatchFormat):
    # TODO: Docs
    def __init__(
        self,
        file_extension: str = ".parquet",
        compress: bool = False,
        compression_type: str = "snappy"  # Parquet compression: snappy, gzip, none, etc.
    ):
        self._compress = compress
        self._compression_type = compression_type if compress else "none"
        self._file_extension = file_extension

    @property
    def file_extension(self) -> str:
        return self._file_extension

    def deserialize_value(self, value: bytes) -> Any:
        # Use pyarrow to load Parquet data
        with BytesIO(value) as f:
            table = pq.read_table(f)
            return table.to_pydict()

    def serialize_batch_values(self, values: SinkBatch) -> tuple[str, bytes]:

        columns = {}


        for row in values:
            for key in row.value:
                if key not in columns:
                    columns[key] = []

                columns[key].append(row.value[key])
                
        # Identify keys that have only None values in their arrays
        none_only_keys = {key for key, values in columns.items() if all(v is None for v in values)}
        
        # Create a new dictionary without the keys that have only None values
        cleaned_data = {key: values for key, values in columns.items() if key not in none_only_keys}
                
                    
        table = pa.Table.from_pydict(cleaned_data)
        with BytesIO() as f:
            pq.write_table(table, f, compression=self._compression_type)
            value_bytes = f.getvalue()

            if self._compress and self._compression_type == "none":  # Handle manual gzip if no Parquet compression
                value_bytes = gzip.compress(value_bytes)

            return value_bytes