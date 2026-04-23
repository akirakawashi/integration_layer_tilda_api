import asyncio
import posixpath
from pathlib import Path

from loguru import logger

from exceptions import (
    NextcloudAppPasswordNotConfiguredError,
    NextcloudBaseUrlNotConfiguredError,
    NextcloudUsernameNotConfiguredError,
)
from infrastructure.dto import StoredFileResult
from infrastructure.uploader.path_utils import (
    build_public_url,
    build_stored_file_name,
    normalize_remote_dir,
)
from infrastructure.uploader.webdav_client import ensure_remote_dir, upload_file
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

        stored_file_name = build_stored_file_name(file_name)
        remote_dir = normalize_remote_dir(self._remote_dir)
        remote_file_path = posixpath.join(remote_dir, stored_file_name) if remote_dir else stored_file_name
        logger.info(
            "Uploading file to Nextcloud: base_url={}, username={}, dav_user_id={}, remote_dir={}, source_file_name={}, stored_file_name={}, content_type={}, size_bytes={}",
            self._base_url,
            self._username,
            self._dav_user_id,
            remote_dir,
            file_name,
            stored_file_name,
            content_type,
            file_path.stat().st_size,
        )

        ensure_remote_dir(
            base_url=self._base_url,
            dav_user_id=self._dav_user_id,
            username=self._username,
            app_password=self._app_password,
            remote_dir=remote_dir,
            timeout_seconds=self._timeout_seconds,
        )
        upload_file(
            base_url=self._base_url,
            dav_user_id=self._dav_user_id,
            username=self._username,
            app_password=self._app_password,
            file_path=file_path,
            remote_file_path=remote_file_path,
            content_type=content_type,
            timeout_seconds=self._timeout_seconds,
        )

        return StoredFileResult(
            stored_file_name=stored_file_name,
            stored_file_path=remote_file_path,
            stored_file_url=build_public_url(self._public_base_url, remote_file_path),
        )

    def _validate_config(self) -> None:
        if not self._base_url:
            raise NextcloudBaseUrlNotConfiguredError()
        if not self._username:
            raise NextcloudUsernameNotConfiguredError()
        if not self._app_password:
            raise NextcloudAppPasswordNotConfiguredError()
