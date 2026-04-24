from secrets import compare_digest

from fastapi import HTTPException, Request, status

from setting import webhook_auth_config


def validate_webhook_api_key(
    *,
    request: Request,
    payload: dict[str, str],
) -> dict[str, str]:
    api_key_name = webhook_auth_config.api_key_name.strip()
    expected_api_key = webhook_auth_config.api_key.get_secret_value()

    sanitized_payload = payload
    if webhook_auth_config.api_key_transport == "post" and api_key_name:
        sanitized_payload = {key: value for key, value in payload.items() if key != api_key_name}

    if not expected_api_key:
        return sanitized_payload

    if not api_key_name:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Некорректная конфигурация webhook API key.",
        )

    if webhook_auth_config.api_key_transport == "header":
        provided_api_key = request.headers.get(api_key_name)
    else:
        provided_api_key = payload.get(api_key_name)

    if provided_api_key is None or not compare_digest(provided_api_key, expected_api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неверный webhook API key.",
        )

    return sanitized_payload
