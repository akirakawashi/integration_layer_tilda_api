from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class DownloadedFile:
    path: Path
    file_name: str
    content_type: str | None = None
    size_bytes: int | None = None
