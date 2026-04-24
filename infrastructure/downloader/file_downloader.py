import asyncio
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

from loguru import logger

from exceptions import EmptyDownloadedFileError, FileTooLargeError, UnsupportedFileFormatError
from infrastructure.downloader.content_validator import validate_downloaded_content
from infrastructure.downloader.file_name_resolver import resolve_file_name
from infrastructure.downloader.request_utils import build_request
from infrastructure.downloader.source_resolver import resolve_download_source
from infrastructure.dto import DownloadedFile
from setting import file_downloader_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class FileDownloader:
    def __init__(self, timeout_seconds: int = 60) -> None:
        self._timeout_seconds = timeout_seconds
        self._max_size_bytes = file_downloader_config.max_size_mb * 1024 * 1024
        self._allowed_extensions = file_downloader_config.allowed_extensions_set

        download_dir = Path(file_downloader_config.dir)
        if not download_dir.is_absolute():
            download_dir = PROJECT_ROOT / download_dir

        download_dir.mkdir(parents=True, exist_ok=True)
        self._download_dir = download_dir

    async def download(self, file_url: str) -> DownloadedFile:
        return await asyncio.to_thread(self._download_sync, file_url)

    def _download_sync(self, file_url: str) -> DownloadedFile:
        resolved_url, suggested_file_name = resolve_download_source(
            file_url,
            timeout_seconds=self._timeout_seconds,
        )
        logger.debug(
            "Downloading file: original_url={}, resolved_url={}, suggested_file_name={}",
            file_url,
            resolved_url,
            suggested_file_name,
        )
        request = build_request(resolved_url)

        temp_path: Path | None = None
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                final_url = getattr(response, "geturl", lambda: resolved_url)()
                content_type = response.headers.get_content_type()
                content_length = response.headers.get("Content-Length")
                logger.debug(
                    (
                        "File download response received: original_url={}, resolved_url={}, "
                        "final_url={}, content_type={}, content_length={}"
                    ),
                    file_url,
                    resolved_url,
                    final_url,
                    content_type,
                    content_length,
                )
                file_name = resolve_file_name(
                    response,
                    resolved_url,
                    suggested_file_name=suggested_file_name,
                )
                suffix = Path(file_name).suffix
                extension = suffix.lower().lstrip(".")
                if extension not in self._allowed_extensions:
                    logger.debug(
                        (
                            "Downloaded file has unsupported extension: file_name={}, "
                            "extension={}, allowed_extensions={}"
                        ),
                        file_name,
                        extension,
                        sorted(self._allowed_extensions),
                    )
                    raise UnsupportedFileFormatError(sorted(self._allowed_extensions))

                temp_file = NamedTemporaryFile(
                    delete=False,
                    suffix=suffix,
                    prefix="tilda_",
                    dir=self._download_dir,
                )
                temp_path = Path(temp_file.name)

                if (
                    content_length is not None
                    and content_length.isdigit()
                    and int(content_length) > self._max_size_bytes
                ):
                    logger.debug(
                        (
                            "Downloaded file exceeds declared size limit: file_name={}, "
                            "declared_size_bytes={}, max_size_bytes={}"
                        ),
                        file_name,
                        content_length,
                        self._max_size_bytes,
                    )
                    raise FileTooLargeError(file_downloader_config.max_size_mb)

                with temp_file:
                    size_bytes = 0
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break

                        size_bytes += len(chunk)
                        if size_bytes > self._max_size_bytes:
                            logger.debug(
                                (
                                    "Downloaded file exceeded size limit while streaming: "
                                    "file_name={}, current_size_bytes={}, max_size_bytes={}"
                                ),
                                file_name,
                                size_bytes,
                                self._max_size_bytes,
                            )
                            raise FileTooLargeError(file_downloader_config.max_size_mb)

                        temp_file.write(chunk)

            if size_bytes == 0:
                logger.debug("Downloaded file is empty: file_name={}, url={}", file_name, resolved_url)
                raise EmptyDownloadedFileError()

            validate_downloaded_content(
                file_path=temp_path,
                file_name=file_name,
                content_type=content_type,
            )
            logger.debug(
                "File download validated successfully: file_name={}, size_bytes={}, temp_path={}",
                file_name,
                size_bytes,
                temp_path,
            )

            return DownloadedFile(
                path=temp_path,
                file_name=file_name,
                content_type=content_type,
                size_bytes=size_bytes,
            )

        except Exception as exc:
            logger.debug(
                "File download failed: original_url={}, resolved_url={}, error_type={}, error_message={}",
                file_url,
                resolved_url,
                type(exc).__name__,
                str(exc),
            )
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
            raise
