from enum import IntEnum


class TildaJobStatusId(IntEnum):
    QUEUED = 1
    PROCESSING = 2
    DONE = 3
    FAILED = 4
    RETRY_WAIT = 5
