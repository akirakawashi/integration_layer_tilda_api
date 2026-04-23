from urllib.error import HTTPError, URLError

from exceptions import (
    DownloadedFileContentMismatchError,
    DownloadedFileNotReadyError,
    DownloadedFileSignatureMismatchError,
    EmptyDownloadedFileError,
    FileTooLargeError,
    NextcloudAppPasswordNotConfiguredError,
    NextcloudAuthenticationFailedError,
    NextcloudBaseUrlNotConfiguredError,
    NextcloudDirectoryCreateFailedError,
    NextcloudUploadFailedError,
    NextcloudUsernameNotConfiguredError,
    UnsupportedFileFormatError,
    UnsupportedFileUrlSchemeError,
)

NON_RETRYABLE_EXCEPTIONS = (
    UnsupportedFileUrlSchemeError,
    UnsupportedFileFormatError,
    FileTooLargeError,
    EmptyDownloadedFileError,
    DownloadedFileContentMismatchError,
    DownloadedFileSignatureMismatchError,
    NextcloudBaseUrlNotConfiguredError,
    NextcloudUsernameNotConfiguredError,
    NextcloudAppPasswordNotConfiguredError,
    NextcloudAuthenticationFailedError,
)

RETRYABLE_EXCEPTIONS = (
    DownloadedFileNotReadyError,
    NextcloudDirectoryCreateFailedError,
    NextcloudUploadFailedError,
)

KNOWN_PROCESSING_EXCEPTIONS = NON_RETRYABLE_EXCEPTIONS + RETRYABLE_EXCEPTIONS


def is_retryable_processing_error(exc: Exception) -> bool:
    if isinstance(exc, NON_RETRYABLE_EXCEPTIONS):
        return False

    if isinstance(exc, HTTPError):
        return exc.code in {408, 429, 500, 502, 503, 504}

    if isinstance(exc, (URLError, TimeoutError, *RETRYABLE_EXCEPTIONS)):
        return True

    return False


def get_processing_error_message(exc: Exception) -> str:
    if isinstance(exc, KNOWN_PROCESSING_EXCEPTIONS):
        return str(exc)

    if isinstance(exc, HTTPError):
        if exc.code == 408:
            return "Удаленный сервер не ответил вовремя при скачивании файла (HTTP 408)."
        if exc.code == 429:
            return "Удаленный сервер временно ограничил количество запросов (HTTP 429)."
        if exc.code in {500, 502, 503, 504}:
            return f"Удаленный сервер временно недоступен (HTTP {exc.code})."
        return f"Не удалось скачать файл по HTTP (HTTP {exc.code})."

    if isinstance(exc, URLError):
        return "Не удалось скачать файл из-за сетевой ошибки."

    if isinstance(exc, TimeoutError):
        return "Превышено время ожидания при скачивании или загрузке файла."

    return str(exc)
