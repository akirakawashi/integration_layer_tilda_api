from urllib.parse import parse_qsl

from fastapi import HTTPException, Request, status

from api.routers.v1.helpers.tilda_payload import extract_tilda_file_url
from api.routers.v1.helpers.webhook_auth import validate_webhook_api_key
from api.routers.v1.shemas import TildaWebhookPayload


async def parse_tilda_webhook_payload(request: Request) -> TildaWebhookPayload:
    payload_bytes = await request.body()
    payload = dict(parse_qsl(payload_bytes.decode("utf-8"), keep_blank_values=True))
    payload = validate_webhook_api_key(request=request, payload=payload)

    webhook_payload = TildaWebhookPayload(
        tranid=payload.get("tranid"),
        formid=payload.get("formid"),
        test=payload.get("test"),
        file_url=extract_tilda_file_url(payload),
        payload=payload,
    )

    if webhook_payload.is_test_request:
        return webhook_payload

    missing_fields = [
        field_name
        for field_name, value in (
            ("tranid", webhook_payload.tran_id),
            ("formid", webhook_payload.form_id),
            ("Прикрепите_файлы", webhook_payload.file_url),
        )
        if not value
    ]
    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Отсутствуют обязательные поля Tilda: {', '.join(missing_fields)}",
        )

    return webhook_payload
