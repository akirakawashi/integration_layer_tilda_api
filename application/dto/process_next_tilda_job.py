from dataclasses import dataclass


@dataclass(slots=True)
class ProcessNextTildaJobCommand:
    worker_id: str = "manual-worker"
    lock_seconds: int = 300


@dataclass(slots=True)
class ProcessNextTildaJobResult:
    processed: bool
    status: str
    message: str
    tilda_job_id: int | None = None
    tran_id: str | None = None
    google_drive_file_id: str | None = None
