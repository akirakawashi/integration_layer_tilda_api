from dataclasses import dataclass


@dataclass(slots=True)
class ProcessNextTildaJobCommand:
    worker_id: str = "manual-worker"
    lock_seconds: int = 300
    retry_delay_seconds: int = 300
    max_attempts: int = 10 # можно убрать


@dataclass(slots=True)
class ProcessNextTildaJobResult:
    processed: bool
    status: str
    message: str
    tilda_job_id: int | None = None
    tran_id: str | None = None
    stored_file_path: str | None = None
    stored_file_url: str | None = None
