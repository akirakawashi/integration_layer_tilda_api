class UnsupportedFileUrlSchemeError(Exception):
    def __init__(self) -> None:
        super().__init__("Поддерживаются только ссылки с протоколом http или https.")


class UnsupportedFileFormatError(Exception):
    def __init__(self, allowed_formats: list[str]) -> None:
        super().__init__(
            "Неподдерживаемый формат файла. Разрешены форматы: "
            f"{', '.join(allowed_formats)}"
        )


class FileTooLargeError(Exception):
    def __init__(self, max_size_mb: int) -> None:
        super().__init__(
            f"Файл слишком большой. Максимально допустимый размер: {max_size_mb} МБ."
        )


class EmptyDownloadedFileError(Exception):
    def __init__(self) -> None:
        super().__init__("Скачанный файл пустой.")
