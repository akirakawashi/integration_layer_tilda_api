from datetime import datetime, timedelta

from loguru import logger

from application.constants.tilda_job_status import TildaJobStatusId
from application.dto.process_next_tilda_job import (
    ProcessNextTildaJobCommand,
    ProcessNextTildaJobResult,
)
from application.mappers import (
    get_processing_error_message,
    is_retryable_processing_error,
)
from infrastructure.database.repository.tilda_job_repository import TildaJobRepository
from infrastructure.dto import DownloadedFile
from infrastructure.file_downloader import FileDownloader
from infrastructure.nextcloud_file_storage import NextcloudFileStorage
from setting import APP_TIMEZONE_INFO


class ProcessNextTildaJob:
    def __init__(
        self,
        repository: TildaJobRepository,
        file_downloader: FileDownloader,
        file_storage: NextcloudFileStorage,
    ) -> None:
        self._repository = repository
        self._file_downloader = file_downloader
        self._file_storage = file_storage

    async def execute(
        self,
        command: ProcessNextTildaJobCommand,
    ) -> ProcessNextTildaJobResult:
        job = await self._repository.claim_next_ready_job(
            queued_status_id=TildaJobStatusId.QUEUED,
            retry_wait_status_id=TildaJobStatusId.RETRY_WAIT,
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

        logger.info(
            "Tilda job claimed: tilda_job_id={}, tran_id={}, attempt_count={}, file_url={}",
            job.tilda_job_id,
            job.tran_id,
            job.attempt_count,
            job.file_url,
        )

        downloaded_file: DownloadedFile | None = None

        try:
            downloaded_file = await self._file_downloader.download(job.file_url)
            logger.info(
                "Tilda job file downloaded: tilda_job_id={}, file_name={}, content_type={}, size_bytes={}, path={}",
                job.tilda_job_id,
                downloaded_file.file_name,
                downloaded_file.content_type,
                downloaded_file.size_bytes,
                downloaded_file.path,
            )

            upload_result = await self._file_storage.store_file(
                file_path=downloaded_file.path,
                file_name=downloaded_file.file_name,
                content_type=downloaded_file.content_type,
            )
            logger.info(
                "Tilda job file stored: tilda_job_id={}, stored_file_name={}, stored_file_path={}, stored_file_url={}",
                job.tilda_job_id,
                upload_result.stored_file_name,
                upload_result.stored_file_path,
                upload_result.stored_file_url,
            )

            await self._repository.mark_done(
                job_id=job.tilda_job_id,
                done_status_id=TildaJobStatusId.DONE,
                stored_file_name=upload_result.stored_file_name,
            )

            return ProcessNextTildaJobResult(
                processed=True,
                status="done",
                message="Tilda job processed successfully",
                tilda_job_id=job.tilda_job_id,
                tran_id=job.tran_id,
                stored_file_name=upload_result.stored_file_name,
                stored_file_path=upload_result.stored_file_path,
                stored_file_url=upload_result.stored_file_url,
            )
        except Exception as exc:
            error_message = get_processing_error_message(exc)
            logger.opt(exception=exc).warning(
                "Tilda job processing failed: tilda_job_id={}, tran_id={}, attempt_count={}, max_attempts={}, error_type={}, error_message={}",
                job.tilda_job_id,
                job.tran_id,
                job.attempt_count,
                command.max_attempts,
                type(exc).__name__,
                error_message,
            )

            if is_retryable_processing_error(exc) and job.attempt_count < command.max_attempts:
                retry_at = datetime.now(APP_TIMEZONE_INFO) + timedelta(seconds=command.retry_delay_seconds)
                logger.info(
                    "Tilda job scheduled for retry: tilda_job_id={}, retry_at={}, retry_delay_seconds={}",
                    job.tilda_job_id,
                    retry_at,
                    command.retry_delay_seconds,
                )
                await self._repository.mark_retry_wait(
                    job_id=job.tilda_job_id,
                    retry_wait_status_id=TildaJobStatusId.RETRY_WAIT,
                    error_message=error_message,
                    retry_at=retry_at,
                )

                return ProcessNextTildaJobResult(
                    processed=True,
                    status="retry_wait",
                    message=error_message,
                    tilda_job_id=job.tilda_job_id,
                    tran_id=job.tran_id,
                )

            logger.info(
                "Tilda job marked as failed: tilda_job_id={}, tran_id={}, attempt_count={}",
                job.tilda_job_id,
                job.tran_id,
                job.attempt_count,
            )
            await self._repository.mark_failed(
                job_id=job.tilda_job_id,
                failed_status_id=TildaJobStatusId.FAILED,
                error_message=error_message,
            )

            return ProcessNextTildaJobResult(
                processed=True,
                status="failed",
                message=error_message,
                tilda_job_id=job.tilda_job_id,
                tran_id=job.tran_id,
            )
        finally:
            if downloaded_file is not None:
                logger.debug(
                    "Removing temporary downloaded file: tilda_job_id={}, path={}",
                    job.tilda_job_id,
                    downloaded_file.path,
                )
                downloaded_file.path.unlink(missing_ok=True)
