from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import TildaJob


class TildaJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_tran_id(self, tran_id: str) -> TildaJob | None:
        statement = select(TildaJob).where(TildaJob.tran_id == tran_id)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

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
