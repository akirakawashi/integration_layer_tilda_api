import asyncio
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

from setting import file_downloader_config


PROJECT_ROOT = Path(__file__).resolve().parent.parent

@dataclass(slots=True)
class DownloadedFile:
    path: Path
    file_name: str
    content_type: str | None = None
    size_bytes: int | None = None


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
            raise ValueError("Only http and https file URLs are supported")

        file_name = Path(unquote(parsed_url.path)).name or "downloaded_file"
        suffix = Path(file_name).suffix
        extension = suffix.lower().lstrip(".")
        if extension not in self._allowed_extensions:
            raise ValueError(
                "Unsupported file format. "
                f"Allowed formats: {', '.join(sorted(self._allowed_extensions))}"
            )

        temp_file = NamedTemporaryFile(
            delete=False,
            suffix=suffix,
            prefix="tilda_",
            dir=self._download_dir,
        )
        temp_path = Path(temp_file.name)

        request = Request(
            file_url,
            headers={
                "User-Agent": "tilda-api-file-downloader/1.0",
            },
        )

        try:
            with temp_file, urlopen(request, timeout=self._timeout_seconds) as response:
                content_type = response.headers.get_content_type()
                content_length = response.headers.get("Content-Length")

                if (
                    content_length is not None
                    and content_length.isdigit()
                    and int(content_length) > self._max_size_bytes
                ):
                    raise ValueError(
                        "File is too large. "
                        f"Maximum allowed size is {file_downloader_config.max_size_mb} MB"
                    )

                size_bytes = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break

                    size_bytes += len(chunk)
                    if size_bytes > self._max_size_bytes:
                        raise ValueError(
                            "File is too large. "
                            f"Maximum allowed size is {file_downloader_config.max_size_mb} MB"
                        )

                    temp_file.write(chunk)

            if size_bytes == 0:
                raise ValueError("Downloaded file is empty")

            return DownloadedFile(
                path=temp_path,
                file_name=file_name,
                content_type=content_type,
                size_bytes=size_bytes,
            )
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise
