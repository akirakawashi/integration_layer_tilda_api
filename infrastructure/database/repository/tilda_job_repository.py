from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import TildaJob


class TildaJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_tran_id(self, tran_id: str) -> TildaJob | None:
        statement = select(TildaJob).where(TildaJob.tran_id == tran_id)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def claim_next_queued_job(
        self,
        *,
        queued_status_id: int,
        processing_status_id: int,
        locked_by: str,
        lock_seconds: int,
    ) -> TildaJob | None:
        statement = (
            select(TildaJob)
            .where(TildaJob.tilda_job_status_id == queued_status_id)
            .where(
                or_(
                    TildaJob.locked_until.is_(None),
                    TildaJob.locked_until < func.now(),
                )
            )
            .order_by(TildaJob.date_create)
            .limit(1)
            .with_for_update(skip_locked=True)
        )

        async with self._session.begin():
            result = await self._session.execute(statement)
            job = result.scalar_one_or_none()

            if job is None:
                return None

            job.tilda_job_status_id = processing_status_id
            job.locked_by = locked_by
            job.locked_until = datetime.now(timezone.utc) + timedelta(
                seconds=lock_seconds
            )
            job.attempt_count += 1
            job.last_error_message = None
            job.next_retry_at = None

        return job

    async def create_job(
        self,
        *,
        tran_id: str,
        form_id: str,
        file_url: str,
        payload: dict[str, str],
        status_id: int,
    ) -> TildaJob:
        job = TildaJob(
            tran_id=tran_id,
            form_id=form_id,
            file_url=file_url,
            payload=payload,
            tilda_job_status_id=status_id,
        )
        self._session.add(job)
        await self._session.commit()
        await self._session.refresh(job)
        return job

    async def mark_done(
        self,
        *,
        job_id: int,
        done_status_id: int,
    ) -> TildaJob:
        async with self._session.begin():
            job = await self._session.get(TildaJob, job_id)

            if job is None:
                raise ValueError(f"Tilda job with id={job_id} was not found")

            job.tilda_job_status_id = done_status_id
            job.locked_by = None
            job.locked_until = None
            job.next_retry_at = None
            job.last_error_message = None

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
                raise ValueError(f"Tilda job with id={job_id} was not found")

            job.tilda_job_status_id = failed_status_id
            job.locked_by = None
            job.locked_until = None
            job.next_retry_at = None
            job.last_error_message = error_message

        return job
