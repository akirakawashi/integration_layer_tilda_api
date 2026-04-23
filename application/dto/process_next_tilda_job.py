from dataclasses import dataclass


@dataclass(slots=True)
class ProcessNextTildaJobCommand:
    worker_id: str
    lock_seconds: int
    retry_delay_seconds: int
    max_attempts: int


@dataclass(slots=True)
class ProcessNextTildaJobResult:
    processed: bool
    status: str
    message: str
    tilda_job_id: int | None = None
    tran_id: str | None = None
    stored_file_name: str | None = None
    stored_file_path: str | None = None
    stored_file_url: str | None = None
