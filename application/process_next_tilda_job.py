from application.constants.tilda_job_status import TildaJobStatusId
from application.dto.process_next_tilda_job import (
    ProcessNextTildaJobCommand,
    ProcessNextTildaJobResult,
)
from infrastructure.database.repository.tilda_job_repository import TildaJobRepository
from infrastructure.file_downloader import DownloadedFile, FileDownloader
from infrastructure.google_drive_client import GoogleDriveClient


class ProcessNextTildaJob:
    def __init__(
        self,
        repository: TildaJobRepository,
        file_downloader: FileDownloader,
        google_drive_client: GoogleDriveClient,
    ) -> None:
        self._repository = repository
        self._file_downloader = file_downloader
        self._google_drive_client = google_drive_client

    async def execute(
        self,
        command: ProcessNextTildaJobCommand,
    ) -> ProcessNextTildaJobResult:
        job = await self._repository.claim_next_queued_job(
            queued_status_id=TildaJobStatusId.QUEUED,
            processing_status_id=TildaJobStatusId.PROCESSING,
            locked_by=command.worker_id,
            lock_seconds=command.lock_seconds,
        )
        if job is None:
            return ProcessNextTildaJobResult(
                processed=False,
                status="idle",
                message="No queued Tilda jobs found",
            )

        downloaded_file: DownloadedFile | None = None

        try:
            downloaded_file = await self._file_downloader.download(job.file_url)
            upload_result = await self._google_drive_client.upload_file(
                file_path=downloaded_file.path,
                file_name=downloaded_file.file_name,
                content_type=downloaded_file.content_type,
            )

            await self._repository.mark_done(
                job_id=job.tilda_job_id,
                done_status_id=TildaJobStatusId.DONE,
            )

            return ProcessNextTildaJobResult(
                processed=True,
                status="done",
                message="Tilda job processed successfully",
                tilda_job_id=job.tilda_job_id,
                tran_id=job.tran_id,
                google_drive_file_id=upload_result.file_id,
            )
        except Exception as exc:
            await self._repository.mark_failed(
                job_id=job.tilda_job_id,
                failed_status_id=TildaJobStatusId.FAILED,
                error_message=str(exc),
            )

            return ProcessNextTildaJobResult(
                processed=True,
                status="failed",
                message=str(exc),
                tilda_job_id=job.tilda_job_id,
                tran_id=job.tran_id,
            )
        finally:
            if downloaded_file is not None:
                downloaded_file.path.unlink(missing_ok=True)
