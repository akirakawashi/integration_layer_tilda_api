from urllib.parse import parse_qsl

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.v1.helpers import extract_tilda_file_url
from application.accept_tilda_webhook import AcceptTildaWebhook
from application.dto.accept_tilda_webhook import AcceptTildaWebhookCommand
from infrastructure.database.provider import DatabaseProvider
from infrastructure.database.repository.tilda_job_repository import TildaJobRepository

router = APIRouter(tags=["tilda"])


@router.post(
    "/webhooks/tilda",
    summary="Accept Tilda webhook",
    response_class=PlainTextResponse,
    status_code=status.HTTP_200_OK,
)
async def accept_tilda_webhook(
    request: Request, session: AsyncSession = Depends(DatabaseProvider.get_session)
) -> PlainTextResponse:
    payload_bytes = await request.body()
    payload = dict(parse_qsl(payload_bytes.decode("utf-8"), keep_blank_values=True))

    if payload.get("test") == "test":
        return PlainTextResponse("ok", status_code=status.HTTP_200_OK)

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
            detail=f"Отсутствуют обязательные поля Tilda: {', '.join(missing_fields)}",
        )
    assert tran_id is not None
    assert form_id is not None
    assert file_url is not None

    use_case = AcceptTildaWebhook(
        repository=TildaJobRepository(session=session),
    )

    await use_case.execute(
        AcceptTildaWebhookCommand(
            tran_id=tran_id,
            form_id=form_id,
            file_url=file_url,
            payload=payload,
        )
    )

    return PlainTextResponse("ok", status_code=status.HTTP_200_OK)
