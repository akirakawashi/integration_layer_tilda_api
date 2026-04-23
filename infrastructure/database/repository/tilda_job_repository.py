from datetime import datetime, timedelta
from typing import cast

from sqlalchemy import Table, and_, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions import TildaJobConflictStateError, TildaJobNotFoundError
from infrastructure.database.models import TildaJob, TildaJobStatusHistory
from setting import APP_TIMEZONE_INFO


class TildaJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _require_job_id(job: TildaJob) -> int:
        job_id = job.tilda_jobs_id
        if job_id is None:
            raise RuntimeError("Persisted Tilda job is missing primary key.")

        return job_id

    @staticmethod
    def _job_table() -> Table:
        return cast(Table, getattr(TildaJob, "__table__"))

    def _add_status_history(
        self,
        *,
        job_id: int,
        status_id: int,
        error_message: str | None = None,
    ) -> None:
        self._session.add(
            TildaJobStatusHistory(
                tilda_jobs_id=job_id,
                tilda_jobs_status_id=status_id,
                error_message=error_message,
            )
        )

    async def claim_next_ready_job(
        self,
        *,
        queued_status_id: int,
        retry_wait_status_id: int,
        processing_status_id: int,
        locked_by: str,
        lock_seconds: int,
    ) -> TildaJob | None:
        job_table = self._job_table()
        statement = (
            select(TildaJob)
            .where(
                or_(
                    job_table.c.tilda_jobs_status_id == queued_status_id,
                    and_(
                        job_table.c.tilda_jobs_status_id == retry_wait_status_id,
                        job_table.c.next_retry_at.is_not(None),
                        job_table.c.next_retry_at <= func.now(),
                    ),
                    and_(
                        job_table.c.tilda_jobs_status_id == processing_status_id,
                        job_table.c.locked_until.is_not(None),
                        job_table.c.locked_until < func.now(),
                    ),
                )
            )
            .where(
                or_(
                    job_table.c.locked_until.is_(None),
                    job_table.c.locked_until < func.now(),
                )
            )
            .order_by(func.coalesce(job_table.c.next_retry_at, job_table.c.date_create))
            .limit(1)
            .with_for_update(skip_locked=True)
        )

        async with self._session.begin():
            result = await self._session.execute(statement)
            job = result.scalar_one_or_none()

            if job is None:
                return None

            job.tilda_jobs_status_id = processing_status_id
            job.locked_by = locked_by
            job.locked_until = datetime.now(APP_TIMEZONE_INFO) + timedelta(seconds=lock_seconds)
            job.attempt_count += 1
            job.last_error_message = None
            job.next_retry_at = None
            job_id = self._require_job_id(job)
            self._add_status_history(
                job_id=job_id,
                status_id=processing_status_id,
            )

        return job

    async def create_job_or_get_existing(
        self,
        *,
        tran_id: str,
        form_id: str,
        file_url: str,
        payload: dict[str, str],
        status_id: int,
    ) -> tuple[TildaJob, bool]:
        job_table = self._job_table()
        async with self._session.begin():
            statement = (
                insert(TildaJob)
                .values(
                    tran_id=tran_id,
                    form_id=form_id,
                    file_url=file_url,
                    payload=payload,
                    tilda_jobs_status_id=status_id,
                )
                .on_conflict_do_nothing(index_elements=[job_table.c.tran_id])
                .returning(TildaJob)
            )
            result = await self._session.execute(statement)
            job = result.scalar_one_or_none()

            if job is not None:
                job_id = self._require_job_id(job)
                self._add_status_history(
                    job_id=job_id,
                    status_id=status_id,
                )
                return job, False

            existing_statement = select(TildaJob).where(job_table.c.tran_id == tran_id)
            existing_result = await self._session.execute(existing_statement)
            existing_job = existing_result.scalar_one_or_none()
            if existing_job is None:
                raise TildaJobConflictStateError(tran_id)

            return existing_job, True

    async def mark_done(
        self,
        *,
        job_id: int,
        done_status_id: int,
        stored_file_name: str,
    ) -> TildaJob:
        async with self._session.begin():
            job = await self._session.get(TildaJob, job_id)

            if job is None:
                raise TildaJobNotFoundError(job_id)

            job.tilda_jobs_status_id = done_status_id
            job.locked_by = None
            job.locked_until = None
            job.next_retry_at = None
            job.last_error_message = None
            job.stored_file_name = stored_file_name
            persisted_job_id = self._require_job_id(job)
            self._add_status_history(
                job_id=persisted_job_id,
                status_id=done_status_id,
            )

        return job

    async def mark_retry_wait(
        self,
        *,
        job_id: int,
        retry_wait_status_id: int,
        error_message: str,
        retry_at: datetime,
    ) -> TildaJob:
        async with self._session.begin():
            job = await self._session.get(TildaJob, job_id)

            if job is None:
                raise TildaJobNotFoundError(job_id)

            job.tilda_jobs_status_id = retry_wait_status_id
            job.locked_by = None
            job.locked_until = None
            job.next_retry_at = retry_at
            job.last_error_message = error_message
            persisted_job_id = self._require_job_id(job)
            self._add_status_history(
                job_id=persisted_job_id,
                status_id=retry_wait_status_id,
                error_message=error_message,
            )

        return job

    async def mark_failed(
        self,
        *,
        job_id: int,
        failed_status_id: int,
        error_message: str,
    ) -> TildaJob:
        async with self._session.begin():
            job = await self._session.get(TildaJob, job_id)

            if job is None:
                raise TildaJobNotFoundError(job_id)

            job.tilda_jobs_status_id = failed_status_id
            job.locked_by = None
            job.locked_until = None
            job.next_retry_at = None
            job.last_error_message = error_message
            persisted_job_id = self._require_job_id(job)
            self._add_status_history(
                job_id=persisted_job_id,
                status_id=failed_status_id,
                error_message=error_message,
            )

        return job
