from urllib.parse import parse_qsl

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from application.accept_tilda_webhook import AcceptTildaWebhook
from application.dto.accept_tilda_webhook import AcceptTildaWebhookCommand
from api.routers.v1.shemas import (
    TildaWebhookAcceptedResponse,
)
from api.routers.v1.helpers import extract_tilda_file_url
from infrastructure.database.provider import DatabaseProvider
from infrastructure.database.repository.tilda_job_repository import TildaJobRepository

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

    if payload.get("test") == "test":
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Tilda webhook test accepted"},
        )

    tran_id = payload.get("tranid")
    form_id = payload.get("formid")
    file_url = extract_tilda_file_url(payload)

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
