from quixstreams.sinks.exceptions import QuixException


class InvalidS3FormatterError(QuixException):
    """
    Raised when S3 formatter is specified incorrectly
    """


class S3SinkSerializationError(QuixException):
    """
    Raise when S3 Sink formatter fails to serialize items in the batch
    """