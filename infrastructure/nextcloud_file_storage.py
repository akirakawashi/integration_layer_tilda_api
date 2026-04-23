import asyncio
import base64
import posixpath
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from loguru import logger

from exceptions import (
    NextcloudAppPasswordNotConfiguredError,
    NextcloudAuthenticationFailedError,
    NextcloudBaseUrlNotConfiguredError,
    NextcloudDirectoryCreateFailedError,
    NextcloudUploadFailedError,
    NextcloudUsernameNotConfiguredError,
)
from infrastructure.dto import StoredFileResult
from setting import nextcloud_storage_config


class NextcloudFileStorage:
    def __init__(self) -> None:
        self._base_url = nextcloud_storage_config.base_url.strip()
        self._username = nextcloud_storage_config.username.strip()
        self._app_password = nextcloud_storage_config.app_password.get_secret_value()
        self._dav_user_id = (nextcloud_storage_config.dav_user_id or self._username).strip()
        self._remote_dir = nextcloud_storage_config.remote_dir.strip()
        self._public_base_url = nextcloud_storage_config.public_base_url
        self._timeout_seconds = nextcloud_storage_config.timeout_seconds

    async def store_file(
        self,
        *,
        file_path: Path,
        file_name: str,
        content_type: str | None = None,
    ) -> StoredFileResult:
        return await asyncio.to_thread(
            self._store_file_sync,
            file_path,
            file_name,
            content_type,
        )

    def _store_file_sync(
        self,
        file_path: Path,
        file_name: str,
        content_type: str | None,
    ) -> StoredFileResult:
        self._validate_config()

        stored_file_name = self._build_stored_file_name(file_name)
        remote_dir = self._normalize_remote_dir(self._remote_dir)
        remote_file_path = posixpath.join(remote_dir, stored_file_name) if remote_dir else stored_file_name

        logger.info(
            "Uploading file to Nextcloud: base_url={}, username={}, remote_dir={}, "
            "dav_user_id={}, source_file_name={}, stored_file_name={}, content_type={}",
            self._base_url,
            self._username,
            remote_dir or ".",
            self._dav_user_id,
            file_name,
            stored_file_name,
            content_type or "application/octet-stream",
        )
        self._ensure_remote_dir(remote_dir)
        self._upload_file(
            file_path=file_path,
            remote_file_path=remote_file_path,
            content_type=content_type,
        )

        return StoredFileResult(
            stored_file_name=stored_file_name,
            stored_file_path=remote_file_path,
            stored_file_url=self._build_public_url(remote_file_path),
        )

    def _validate_config(self) -> None:
        if not self._base_url:
            raise NextcloudBaseUrlNotConfiguredError()
        if not self._username:
            raise NextcloudUsernameNotConfiguredError()
        if not self._app_password:
            raise NextcloudAppPasswordNotConfiguredError()

    def _build_stored_file_name(self, file_name: str) -> str:
        suffix = Path(file_name).suffix.lower()
        return f"{uuid.uuid4().hex}{suffix}"

    def _normalize_remote_dir(self, remote_dir: str) -> str:
        normalized = posixpath.normpath(remote_dir.strip("/"))
        return "" if normalized == "." else normalized

    def _ensure_remote_dir(self, remote_dir: str) -> None:
        if not remote_dir:
            logger.debug("Nextcloud remote directory is empty, skipping MKCOL")
            return

        current_parts: list[str] = []
        for part in remote_dir.split("/"):
            if not part:
                continue

            current_parts.append(part)
            directory_path = "/".join(current_parts)
            request = Request(
                self._build_webdav_url(directory_path),
                headers=self._build_auth_headers(),
                method="MKCOL",
            )

            try:
                logger.debug("Ensuring Nextcloud directory exists: {}", directory_path)
                with urlopen(request, timeout=self._timeout_seconds) as response:
                    logger.debug(
                        "Nextcloud MKCOL response: directory={}, status={}",
                        directory_path,
                        response.status,
                    )
                    if response.status != 201:
                        raise NextcloudDirectoryCreateFailedError(response.status)
            except HTTPError as exc:
                if exc.code == 405:
                    logger.debug("Nextcloud directory already exists: {}", directory_path)
                    continue
                if exc.code in {401, 403}:
                    logger.warning(
                        "Nextcloud authentication failed while creating directory: directory={}, status={}",
                        directory_path,
                        exc.code,
                    )
                    raise NextcloudAuthenticationFailedError() from exc
                logger.warning(
                    "Nextcloud directory creation failed: directory={}, status={}",
                    directory_path,
                    exc.code,
                )
                raise NextcloudDirectoryCreateFailedError(exc.code) from exc
            except (TimeoutError, URLError, OSError) as exc:
                logger.warning(
                    "Nextcloud directory creation failed: directory={}, error={}",
                    directory_path,
                    exc,
                )
                raise NextcloudDirectoryCreateFailedError() from exc

    def _upload_file(
        self,
        *,
        file_path: Path,
        remote_file_path: str,
        content_type: str | None,
    ) -> None:
        headers = self._build_auth_headers()
        headers["Content-Type"] = content_type or "application/octet-stream"

        request = Request(
            self._build_webdav_url(remote_file_path),
            data=file_path.read_bytes(),
            headers=headers,
            method="PUT",
        )

        try:
            logger.debug("Uploading file to Nextcloud path: {}", remote_file_path)
            with urlopen(request, timeout=self._timeout_seconds) as response:
                logger.debug(
                    "Nextcloud PUT response: remote_file_path={}, status={}",
                    remote_file_path,
                    response.status,
                )
                if response.status not in {200, 201, 204}:
                    raise NextcloudUploadFailedError(response.status)
        except HTTPError as exc:
            if exc.code in {401, 403}:
                logger.warning(
                    "Nextcloud authentication failed while uploading file: remote_file_path={}, status={}",
                    remote_file_path,
                    exc.code,
                )
                raise NextcloudAuthenticationFailedError() from exc
            logger.warning(
                "Nextcloud upload failed: remote_file_path={}, status={}",
                remote_file_path,
                exc.code,
            )
            raise NextcloudUploadFailedError(exc.code) from exc
        except (TimeoutError, URLError, OSError) as exc:
            logger.warning(
                "Nextcloud upload failed: remote_file_path={}, error={}",
                remote_file_path,
                exc,
            )
            raise NextcloudUploadFailedError() from exc

    def _build_auth_headers(self) -> dict[str, str]:
        credentials = f"{self._username}:{self._app_password}".encode("utf-8")
        auth_token = base64.b64encode(credentials).decode("ascii")
        return {"Authorization": f"Basic {auth_token}"}

    def _build_webdav_url(self, remote_path: str) -> str:
        webdav_root = f"{self._base_url.rstrip('/')}/remote.php/dav/files/{quote(self._dav_user_id, safe='')}"
        quoted_path = self._quote_remote_path(remote_path)

        if not quoted_path:
            return webdav_root

        return f"{webdav_root}/{quoted_path}"

    def _quote_remote_path(self, remote_path: str) -> str:
        return "/".join(quote(part, safe="") for part in remote_path.split("/") if part)

    def _build_public_url(self, remote_file_path: str) -> str | None:
        if not self._public_base_url:
            return None

        return f"{self._public_base_url.rstrip('/')}/{self._quote_remote_path(remote_file_path)}"
