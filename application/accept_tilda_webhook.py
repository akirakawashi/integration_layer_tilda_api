from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class AcceptTildaWebhookCommand:
    tran_id: str
    form_id: str
    file_url: str
    payload: dict[str, str]


@dataclass(slots=True)
class AcceptTildaWebhookResult:
    tilda_job_id: int
    tran_id: str
    duplicate: bool = False


class TildaJobRepositoryProtocol(Protocol):
    async def get_by_tran_id(self, tran_id: str): ...

    async def get_status_id_by_code(self, status_code: str) -> int: ...

    async def create_job(
        self,
        *,
        tran_id: str,
        form_id: str,
        file_url: str,
        payload: dict[str, str],
        status_id: int,
    ): ...


class AcceptTildaWebhook:
    def __init__(self, repository: TildaJobRepositoryProtocol) -> None:
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

        queued_status_id = await self._repository.get_status_id_by_code("queued")
        job = await self._repository.create_job(
            tran_id=command.tran_id,
            form_id=command.form_id,
            file_url=command.file_url,
            payload=command.payload,
            status_id=queued_status_id,
        )

        return AcceptTildaWebhookResult(
            tilda_job_id=job.tilda_job_id,
            tran_id=job.tran_id,
        )
