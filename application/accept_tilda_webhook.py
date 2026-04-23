from application.constants.tilda_job_status import TildaJobStatusId
from application.dto.accept_tilda_webhook import (
    AcceptTildaWebhookCommand,
    AcceptTildaWebhookResult,
)
from infrastructure.database.repository.tilda_job_repository import TildaJobRepository


class AcceptTildaWebhook:
    def __init__(self, repository: TildaJobRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        command: AcceptTildaWebhookCommand,
    ) -> AcceptTildaWebhookResult:
        job, duplicate = await self._repository.create_job_or_get_existing(
            tran_id=command.tran_id,
            form_id=command.form_id,
            file_url=command.file_url,
            payload=command.payload,
            status_id=TildaJobStatusId.QUEUED,
        )
        job_id = job.tilda_job_id
        if job_id is None:
            raise RuntimeError("Persisted Tilda job is missing primary key.")

        if duplicate:
            return AcceptTildaWebhookResult(
                tilda_job_id=job_id,
                tran_id=job.tran_id,
                duplicate=True,
            )

        return AcceptTildaWebhookResult(
            tilda_job_id=job_id,
            tran_id=job.tran_id,
        )
