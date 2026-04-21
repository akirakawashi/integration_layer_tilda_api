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
        existing_job = await self._repository.get_by_tran_id(command.tran_id)
        if existing_job is not None:
            return AcceptTildaWebhookResult(
                tilda_job_id=existing_job.tilda_job_id,
                tran_id=existing_job.tran_id,
                duplicate=True,
            )

        job = await self._repository.create_job(
            tran_id=command.tran_id,
            form_id=command.form_id,
            file_url=command.file_url,
            payload=command.payload,
            status_id=TildaJobStatusId.QUEUED,
        )

        return AcceptTildaWebhookResult(
            tilda_job_id=job.tilda_job_id,
            tran_id=job.tran_id,
        )
