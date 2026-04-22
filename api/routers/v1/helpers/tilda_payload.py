def extract_tilda_file_url(payload: dict[str, str]) -> str | None:
    explicit_field_names = (
        "Прикрепите_файлы",
        "Прикрепите_файл_архив_с_документами",
    )
    for field_name in explicit_field_names:
        value = payload.get(field_name)
        if value:
            return value

    for field_name, value in payload.items():
        normalized_field_name = field_name.lower()
        if (
            value
            and value.startswith(("http://", "https://"))
            and any(
                marker in normalized_field_name
                for marker in ("прикрепите", "файл", "архив", "документ", "upload")
            )
        ):
            return value

    return None
