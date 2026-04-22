from urllib.parse import parse_qsl

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.accept_tilda_webhook import AcceptTildaWebhook
from application.dto.accept_tilda_webhook import AcceptTildaWebhookCommand
from application.dto.process_next_tilda_job import ProcessNextTildaJobCommand
from application.process_next_tilda_job import ProcessNextTildaJob
from api.routers.v1.shemas import (
    ProcessNextTildaJobResponse,
    TildaWebhookAcceptedResponse,
)
from infrastructure.database.provider import DatabaseProvider
from infrastructure.database.repository.tilda_job_repository import TildaJobRepository
from infrastructure.file_downloader import FileDownloader
from infrastructure.google_drive_client import GoogleDriveClient

router = APIRouter(tags=["tilda"])

@router.post(
    "/webhooks/tilda",
    summary="Accept Tilda webhook",
    response_model=TildaWebhookAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def accept_tilda_webhook(
    request: Request,
    session: AsyncSession = Depends(DatabaseProvider.get_session)
) -> TildaWebhookAcceptedResponse:
    payload_bytes = await request.body()
    payload = dict(parse_qsl(payload_bytes.decode("utf-8"), keep_blank_values=True))

    tran_id = payload.get("tranid")
    form_id = payload.get("formid")
    file_url = payload.get("Прикрепите_файлы")

    missing_fields = [
        field_name
        for field_name, value in (
            ("tranid", tran_id),
            ("formid", form_id),
            ("Прикрепите_файлы", file_url),
        )
        if not value
    ]
    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required Tilda fields: {', '.join(missing_fields)}",
        )

    use_case = AcceptTildaWebhook(
        repository=TildaJobRepository(session=session),
    )

    result = await use_case.execute(
        AcceptTildaWebhookCommand(
            tran_id=tran_id,
            form_id=form_id,
            file_url=file_url,
            payload=payload,
        )
    )

    return TildaWebhookAcceptedResponse(
        tilda_job_id=result.tilda_job_id,
        tran_id=result.tran_id,
        duplicate=result.duplicate,
    )


@router.post(
    "/jobs/process-next",
    summary="Process the next queued Tilda job",
    response_model=ProcessNextTildaJobResponse,
    status_code=status.HTTP_200_OK,
)
async def process_next_tilda_job(
    session: AsyncSession = Depends(DatabaseProvider.get_session)
) -> ProcessNextTildaJobResponse:
    use_case = ProcessNextTildaJob(
        repository=TildaJobRepository(session=session),
        file_downloader=FileDownloader(),
        google_drive_client=GoogleDriveClient(),
    )

    result = await use_case.execute(
        ProcessNextTildaJobCommand(worker_id="api-manual-worker")
    )

    return ProcessNextTildaJobResponse(
        processed=result.processed,
        status=result.status,
        message=result.message,
        tilda_job_id=result.tilda_job_id,
        tran_id=result.tran_id,
        google_drive_file_id=result.google_drive_file_id,
    )
