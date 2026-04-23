import asyncio
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

from exceptions import (
    EmptyDownloadedFileError,
    FileTooLargeError,
    UnsupportedFileFormatError,
    UnsupportedFileUrlSchemeError,
)
from infrastructure.dto import DownloadedFile
from setting import file_downloader_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent


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
        parsed_url = urlparse(file_url)
        if parsed_url.scheme not in {"http", "https"}:
            raise UnsupportedFileUrlSchemeError()

        request = Request(
            file_url,
            headers={
                "User-Agent": "tilda-api-file-downloader/1.0",
            },
        )

        temp_path: Path | None = None
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                file_name = self._resolve_file_name(response, file_url)
                suffix = Path(file_name).suffix
                extension = suffix.lower().lstrip(".")
                if extension not in self._allowed_extensions:
                    raise UnsupportedFileFormatError(sorted(self._allowed_extensions))

                temp_file = NamedTemporaryFile(
                    delete=False,
                    suffix=suffix,
                    prefix="tilda_",
                    dir=self._download_dir,
                )
                temp_path = Path(temp_file.name)
                content_type = response.headers.get_content_type()
                content_length = response.headers.get("Content-Length")

                if (
                    content_length is not None
                    and content_length.isdigit()
                    and int(content_length) > self._max_size_bytes
                ):
                    raise FileTooLargeError(file_downloader_config.max_size_mb)

                with temp_file:
                    size_bytes = 0
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break

                        size_bytes += len(chunk)
                        if size_bytes > self._max_size_bytes:
                            raise FileTooLargeError(file_downloader_config.max_size_mb)

                        temp_file.write(chunk)

            if size_bytes == 0:
                raise EmptyDownloadedFileError()

            return DownloadedFile(
                path=temp_path,
                file_name=file_name,
                content_type=content_type,
                size_bytes=size_bytes,
            )

        except Exception:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
            raise

    def _resolve_file_name(self, response, original_url: str) -> str:
        header_file_name = response.headers.get_filename()
        if header_file_name:
            return Path(unquote(header_file_name)).name

        final_url = getattr(response, "geturl", lambda: original_url)()
        final_file_name = Path(unquote(urlparse(final_url).path)).name
        if final_file_name:
            return final_file_name

        original_file_name = Path(unquote(urlparse(original_url).path)).name
        if original_file_name:
            return original_file_name

        return "downloaded_file"
