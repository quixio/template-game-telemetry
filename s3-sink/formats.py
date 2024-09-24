import abc
import json
from gzip import compress as gzip_compress
from io import BytesIO
from typing import Optional, Callable, Any, List

from jsonlines import Writer
from datetime import datetime

__all__ = ("S3SinkBatchFormat", "JSONFormat", "BytesFormat", "ParquetFormat")


# TODO: Document the compatible topic formats for each formatter
# TODO: Check the types of the values before serializing


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
    def serialize_batch_values(self, values: List[Any]) -> bytes:
        ...


class BytesFormat(S3SinkBatchFormat):
    """
    Bypass formatter to serialize
    """

    def __init__(
        self,
        separator: bytes = b"\n",
        file_extension: str = ".bin",
        compress: bool = False,
    ):
        self._separator = separator
        self._file_extension = file_extension
        self._compress = compress
        if self._compress:
            self._file_extension += ".gz"

    @property
    def file_extension(self) -> str:
        return self._file_extension

    def deserialize_value(self, value: bytes) -> Any:
        return value

    def serialize_batch_values(self, values: List[bytes]) -> bytes:
        value_bytes = self._separator.join(values)
        if self._compress:
            value_bytes = gzip_compress(value_bytes)
        return value_bytes


class JSONFormat(S3SinkBatchFormat):
    # TODO: Docs
    def __init__(
        self,
        dumps: Optional[Callable[[Any], bytes]] = None,
        loads: Optional[Callable[[bytes], Any]] = None,
        file_extension: str = ".json",
        compress: bool = False,
    ):
        self._dumps = dumps or json.dumps
        self._loads = loads or json.loads
        self._compress = compress
        self._file_extension = file_extension
        if self._compress:
            self._file_extension += ".gz"

    @property
    def file_extension(self) -> str:
        return self._file_extension

    def deserialize_value(self, value: bytes) -> Any:
        # TODO: Wrap an exception with more info here
        return self._loads(value)

    def serialize_batch_values(self, values: List[Any]) -> bytes:
        with BytesIO() as f:
            with Writer(f, compact=True, dumps=self._dumps) as writer:
                writer.write_all(values)
            value_bytes = f.getvalue()
            if self._compress:
                value_bytes = gzip_compress(value_bytes)
            return value_bytes
        

import pyarrow as pa
import pyarrow.parquet as pq
from io import BytesIO
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

    def serialize_batch_values(self, values: List[Any]) -> bytes:
        # Get all unique keys (columns) across all rows
        all_keys = set()
        for row in values:
            all_keys.update(row.value.keys())

        # Normalize rows: Ensure all rows have the same keys, filling missing ones with None
        normalized_values = [
            {key: row.value.get(key, None) for key in all_keys} for row in values
        ]

        columns = {
            "_timestamp": [datetime.fromtimestamp(row.timestamp / 1000.0) for row in values], 
            "_key": [bytes.decode(row.key) for row in values]
        }

        # Convert normalized values to a pyarrow Table
        columns = {**columns, **{key: [row[key] for row in normalized_values] for key in all_keys}}
                   
        table = pa.Table.from_pydict(columns)

        with BytesIO() as f:
            pq.write_table(table, f, compression=self._compression_type)
            value_bytes = f.getvalue()

            if self._compress and self._compression_type == "none":  # Handle manual gzip if no Parquet compression
                value_bytes = gzip.compress(value_bytes)

            return value_bytes