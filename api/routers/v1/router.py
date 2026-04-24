from fastapi import APIRouter, Depends, status
from fastapi.responses import PlainTextResponse

from api.routers.v1.helpers import parse_tilda_webhook_payload
from api.routers.v1.shemas import TildaWebhookPayload
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
    webhook_payload: TildaWebhookPayload = Depends(parse_tilda_webhook_payload),
) -> PlainTextResponse:
    if webhook_payload.is_test_request:
        return PlainTextResponse("ok", status_code=status.HTTP_200_OK)

    assert webhook_payload.tran_id is not None
    assert webhook_payload.form_id is not None
    assert webhook_payload.file_url is not None

    async with DatabaseProvider.session_lifecycle() as session:
        use_case = AcceptTildaWebhook(
            repository=TildaJobRepository(session=session),
        )

        await use_case.execute(
            AcceptTildaWebhookCommand(
                tran_id=webhook_payload.tran_id,
                form_id=webhook_payload.form_id,
                file_url=webhook_payload.file_url,
                payload=webhook_payload.payload,
            )
        )

    return PlainTextResponse("ok", status_code=status.HTTP_200_OK)
