from datetime import datetime
import json
import logging
from logging import Logger
import time
from exceptions import InvalidS3FormatterError
import boto3
from botocore.config import Config
import json
from quixstreams.sinks import SinkBatch, BatchingSink
from formats import S3SinkBatchFormat, JSONFormat, BytesFormat

import logging
from io import BytesIO
from pathlib import PurePath
from typing import Union, Any, Literal, Optional, Dict


logger = logging.getLogger("quixstreams")

# TODO: Figure out the best way to create Quix vs non-Quix app
# TODO: Skipping for now:
#  - What to do with keys and timestamps?
# TODO: Timestamp extraction - will be needed for Influx sink 100%.


S3FormatSpec = Literal["bytes", "json"]
_S3_SINK_FORMATTERS: Dict[S3FormatSpec, S3SinkBatchFormat] = {
    "json": JSONFormat(),
    "bytes": BytesFormat(),
}

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
         s3_bucket_name: str,
        s3_access_key_id: str,
        s3_secret_access_key: str,
        format: Union[S3FormatSpec, S3SinkBatchFormat],
        prefix: str = "",
        s3_region_name: Optional[str] = None,
        s3_retry_max_attempts: int = 3,
        s3_connect_timeout: Union[int, float] = 60,
        s3_read_timeout: Union[int, float] = 60,
        loglevel: LogLevel = "INFO"
    ):
        super().__init__()

        self._prefix = prefix
        self._format = self._resolve_format(formatter_spec=format)

        self._s3_bucket_name = s3_bucket_name
        self._s3_client = boto3.client(
            "s3",
            aws_access_key_id=s3_access_key_id,
            aws_secret_access_key=s3_secret_access_key,
            region_name=s3_region_name,
            config=Config(
                read_timeout=s3_read_timeout,
                connect_timeout=s3_connect_timeout,
                retries={"max_attempts": s3_retry_max_attempts, "mode": "standard"},
            ),
        )
        
        # Configure logging.
        self._logger = logging.getLogger("AwsKinesisSink")
        log_format = '[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(name)s] : %(message)s'
        logging.basicConfig(format=log_format, datefmt='%Y-%m-%d %H:%M:%S')
        self._logger.setLevel(loglevel)
        
    

    def build_bucket_file_path(self, topic: str, item) -> str:
        """
        Build a file path for the batch in the S3 bucket

        :param batch: the `Batch` object to be flushed
        :return: file path in the bucket as string

        """
        dir_path = PurePath(self._prefix) / topic
        filename = (
            f"{bytes.decode(item.key)}{self._format.file_extension}"
        )
        path = dir_path / filename
        return path.as_posix()

    def upload(self, path: str, content: dict[bytes]):
        """
        Upload serialized batch to S3 bucket
        """

        for file in content:
        
            logger.info(
                f"Uploading batch to an S3 bucket "
                f's3_bucket_name="{self._s3_bucket_name}" '
                f'path="{path}'
            )
            self._s3_client.upload_fileobj(BytesIO(content[file]), self._s3_bucket_name, path)
            logger.info(
                f"Batch upload complete "
                f's3_bucket_name="{self._s3_bucket_name}" '
        )
        

    def write(self, batch: SinkBatch):
        
        files = {}
        
        for item in batch:
            path = self.build_bucket_file_path(topic=batch.topic, item=item)
            if path not in files:
                files[path] = []
            files[path].append(item.value)

        for file in files:
            files[file] = self._format.serialize_batch_values(files[file])
            
        # Upload batch to S3
        self.upload(path=path, content=files)
        
        
    def _resolve_format(
        self,
        formatter_spec: Union[Literal["bytes"], Literal["json"], S3SinkBatchFormat],
    ) -> S3SinkBatchFormat:
        if isinstance(formatter_spec, S3SinkBatchFormat):
            return formatter_spec

        formatter_obj = _S3_SINK_FORMATTERS.get(formatter_spec)
        if formatter_obj is None:
            raise InvalidS3FormatterError(
                f'Invalid format name "{formatter_obj}". '
                f'Allowed values: "json", "bytes", '
                f"or an instance of {S3SinkBatchFormat.__class__.__name__} "
            )
        return formatter_obj