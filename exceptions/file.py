class UnsupportedFileUrlSchemeError(Exception):
    def __init__(self) -> None:
        super().__init__("Поддерживаются только ссылки с протоколом http или https.")


class UnsupportedFileFormatError(Exception):
    def __init__(self, allowed_formats: list[str]) -> None:
        super().__init__(f"Неподдерживаемый формат файла. Разрешены форматы: {', '.join(allowed_formats)}")


class FileTooLargeError(Exception):
    def __init__(self, max_size_mb: int) -> None:
        super().__init__(f"Файл слишком большой. Максимально допустимый размер: {max_size_mb} МБ.")


class EmptyDownloadedFileError(Exception):
    def __init__(self) -> None:
        super().__init__("Скачанный файл пустой.")


class DownloadedFileNotReadyError(Exception):
    def __init__(self, file_name: str) -> None:
        super().__init__(f"Файл {file_name} еще не готов на стороне Tilda. Попробуем скачать позже.")


class DownloadedFileContentMismatchError(Exception):
    def __init__(self, file_name: str) -> None:
        super().__init__(f"По ссылке на файл {file_name} пришла HTML-страница вместо файла.")


class DownloadedFileSignatureMismatchError(Exception):
    def __init__(self, file_name: str, expected_format: str) -> None:
        super().__init__(
            f"Содержимое файла {file_name} не соответствует заявленному формату {expected_format}."
        )
