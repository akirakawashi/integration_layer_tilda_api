from dataclasses import dataclass


@dataclass(slots=True)
class StoredFileResult:
    stored_file_path: str
    stored_file_url: str | None = None
