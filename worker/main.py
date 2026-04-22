import asyncio
import signal

from loguru import logger

from application.dto.process_next_tilda_job import (
    ProcessNextTildaJobCommand,
    ProcessNextTildaJobResult,
)
from application.process_next_tilda_job import ProcessNextTildaJob
from infrastructure.database.provider import DatabaseProvider
from infrastructure.database.repository.tilda_job_repository import TildaJobRepository
from infrastructure.file_downloader import FileDownloader
from infrastructure.vps_file_storage import VpsFileStorage
from setting import worker_config


class TildaJobWorker:
    def __init__(
        self,
        *,
        stop_event: asyncio.Event | None = None,
    ) -> None:
        self._stop_event = stop_event or asyncio.Event()
        self._file_downloader = FileDownloader()
        self._file_storage = VpsFileStorage()
        self._command = ProcessNextTildaJobCommand(
            worker_id=worker_config.id,
            lock_seconds=worker_config.lock_seconds,
            retry_delay_seconds=worker_config.retry_delay_seconds,
            max_attempts=worker_config.max_attempts,
        )

    async def run_forever(self) -> None:
        logger.info(
            "Starting Tilda worker: worker_id={}, poll_interval={}s",
            worker_config.id,
            worker_config.poll_interval_seconds,
        )

        while not self._stop_event.is_set():
            try:
                result = await self._process_one_job()
            except Exception:
                logger.exception("Unexpected error in Tilda worker loop")
                await self._sleep_or_stop(worker_config.error_backoff_seconds)
                continue

            if not result.processed:
                logger.debug("Tilda worker is idle: no ready jobs found")
                await self._sleep_or_stop(worker_config.poll_interval_seconds)
                continue

            logger.info(
                "Tilda worker processed job: status={}, tilda_job_id={}, tran_id={}",
                result.status,
                result.tilda_job_id,
                result.tran_id,
            )

        logger.info("Tilda worker stop signal received")

    async def _process_one_job(self) -> ProcessNextTildaJobResult:
        async with DatabaseProvider.session_lifecycle() as session:
            use_case = ProcessNextTildaJob(
                repository=TildaJobRepository(session=session),
                file_downloader=self._file_downloader,
                file_storage=self._file_storage,
            )
            return await use_case.execute(self._command)

    async def _sleep_or_stop(self, seconds: int) -> None:
        if seconds <= 0:
            return

        try:
            await asyncio.wait_for(self._stop_event.wait(), timeout=seconds)
        except TimeoutError:
            return


async def async_main() -> None:
    stop_event = asyncio.Event()
    _install_signal_handlers(stop_event)

    await DatabaseProvider.init_engine()
    worker = TildaJobWorker(stop_event=stop_event)

    try:
        await worker.run_forever()
    finally:
        try:
            await asyncio.wait_for(
                DatabaseProvider.dispose_engine(),
                timeout=worker_config.shutdown_grace_seconds,
            )
        except TimeoutError:
            logger.warning(
                "Timed out while disposing database engine during worker shutdown"
            )


def main() -> None:
    asyncio.run(async_main())


def _install_signal_handlers(stop_event: asyncio.Event) -> None:
    loop = asyncio.get_running_loop()

    def request_stop() -> None:
        if not stop_event.is_set():
            logger.info("Shutdown signal received, stopping Tilda worker")
            stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, request_stop)
        except NotImplementedError:
            signal.signal(sig, lambda *_args: request_stop())


if __name__ == "__main__":
    main()
