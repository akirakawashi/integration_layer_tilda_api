import asyncio
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

from setting import google_drive_config


@dataclass(slots=True)
class GoogleDriveUploadResult:
    file_id: str
    web_view_link: str | None = None


class GoogleDriveClient:
    def __init__(self) -> None:
        self._access_token = google_drive_config.access_token.get_secret_value()
        self._folder_id = google_drive_config.folder_id
        self._timeout_seconds = google_drive_config.timeout_seconds

    async def upload_file(
        self,
        *,
        file_path: Path,
        file_name: str,
        content_type: str | None = None,
    ) -> GoogleDriveUploadResult:
        return await asyncio.to_thread(
            self._upload_file_sync,
            file_path,
            file_name,
            content_type,
        )

    def _upload_file_sync(
        self,
        file_path: Path,
        file_name: str,
        content_type: str | None = None,
    ) -> GoogleDriveUploadResult:
        if not self._access_token:
            raise RuntimeError("Google Drive access token is not configured")

        metadata: dict[str, object] = {"name": file_name}
        if self._folder_id:
            metadata["parents"] = [self._folder_id]

        boundary = f"===============tilda-{uuid.uuid4().hex}=="
        resolved_content_type = content_type or "application/octet-stream"
        file_bytes = file_path.read_bytes()
        metadata_bytes = json.dumps(metadata).encode("utf-8")

        body = b"".join(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                b"Content-Type: application/json; charset=UTF-8\r\n\r\n",
                metadata_bytes,
                b"\r\n",
                f"--{boundary}\r\n".encode("utf-8"),
                f"Content-Type: {resolved_content_type}\r\n\r\n".encode("utf-8"),
                file_bytes,
                b"\r\n",
                f"--{boundary}--\r\n".encode("utf-8"),
            ]
        )

        request = Request(
            "https://www.googleapis.com/upload/drive/v3/files"
            "?uploadType=multipart"
            "&supportsAllDrives=true"
            "&fields=id,webViewLink",
            data=body,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": f"multipart/related; boundary={boundary}",
                "Content-Length": str(len(body)),
            },
            method="POST",
        )

        with urlopen(request, timeout=self._timeout_seconds) as response:
            raw_payload = response.read()

        payload = json.loads(raw_payload.decode("utf-8"))

        return GoogleDriveUploadResult(
            file_id=payload["id"],
            web_view_link=payload.get("webViewLink"),
        )
