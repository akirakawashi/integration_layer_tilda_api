import asyncio
import posixpath
import socket
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from setting import vps_storage_config


class VpsStorageConfigurationError(RuntimeError):
    pass


class VpsStorageTemporaryError(RuntimeError):
    pass


@dataclass(slots=True)
class StoredFileResult:
    stored_file_path: str
    stored_file_url: str | None = None


class VpsFileStorage:
    def __init__(self) -> None:
        self._host = vps_storage_config.host
        self._port = vps_storage_config.port
        self._username = vps_storage_config.username
        self._password = vps_storage_config.password.get_secret_value()
        self._private_key_path = vps_storage_config.private_key_path
        self._remote_dir = vps_storage_config.remote_dir.strip()
        self._public_base_url = vps_storage_config.public_base_url
        self._timeout_seconds = vps_storage_config.timeout_seconds

    async def store_file(
        self,
        *,
        file_path: Path,
        file_name: str,
        content_type: str | None = None,
    ) -> StoredFileResult:
        del content_type
        return await asyncio.to_thread(
            self._store_file_sync,
            file_path,
            file_name,
        )

    def _store_file_sync(
        self,
        file_path: Path,
        file_name: str,
    ) -> StoredFileResult:
        if not self._host:
            raise VpsStorageConfigurationError("VPS storage host is not configured")
        if not self._username:
            raise VpsStorageConfigurationError("VPS storage username is not configured")
        if not self._password and not self._private_key_path:
            raise VpsStorageConfigurationError(
                "VPS storage password or private key path is not configured"
            )

        try:
            import paramiko
        except ImportError as exc:
            raise VpsStorageConfigurationError(
                "paramiko is not installed; run poetry install"
            ) from exc

        if self._private_key_path and not Path(self._private_key_path).exists():
            raise VpsStorageConfigurationError(
                f"VPS storage private key was not found: {self._private_key_path}"
            )

        remote_file_name = self._build_remote_file_name(file_name)
        remote_dir = self._normalize_remote_dir(self._remote_dir)
        remote_file_path = posixpath.join(remote_dir, remote_file_name)
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            "hostname": self._host,
            "port": self._port,
            "username": self._username,
            "timeout": self._timeout_seconds,
            "banner_timeout": self._timeout_seconds,
            "auth_timeout": self._timeout_seconds,
        }
        if self._private_key_path:
            connect_kwargs["key_filename"] = self._private_key_path
            if self._password:
                connect_kwargs["passphrase"] = self._password
        else:
            connect_kwargs["password"] = self._password

        try:
            ssh_client.connect(**connect_kwargs)
            sftp_client = ssh_client.open_sftp()
            try:
                self._ensure_remote_dir(sftp_client, remote_dir)
                sftp_client.put(str(file_path), remote_file_path)
            finally:
                sftp_client.close()
        except paramiko.AuthenticationException as exc:
            raise VpsStorageConfigurationError(
                "VPS storage authentication failed"
            ) from exc
        except (paramiko.SSHException, socket.timeout, OSError) as exc:
            raise VpsStorageTemporaryError(
                f"VPS storage upload failed: {exc}"
            ) from exc
        finally:
            ssh_client.close()

        return StoredFileResult(
            stored_file_path=remote_file_path,
            stored_file_url=self._build_public_url(remote_file_path),
        )

    def _build_remote_file_name(self, file_name: str) -> str:
        suffix = Path(file_name).suffix.lower()
        return f"{uuid.uuid4().hex}{suffix}"

    def _normalize_remote_dir(self, remote_dir: str) -> str:
        normalized = posixpath.normpath(remote_dir or ".")
        return normalized if normalized != "." else ""

    def _ensure_remote_dir(self, sftp_client, remote_dir: str) -> None:
        if not remote_dir:
            return

        parts = [part for part in remote_dir.split("/") if part]
        current = "/" if remote_dir.startswith("/") else ""

        for part in parts:
            current = posixpath.join(current, part) if current else part
            try:
                sftp_client.stat(current)
            except OSError:
                sftp_client.mkdir(current)

    def _build_public_url(self, remote_file_path: str) -> str | None:
        if not self._public_base_url:
            return None

        relative_path = remote_file_path.lstrip("/")
        return (
            f"{self._public_base_url.rstrip('/')}/"
            f"{quote(relative_path, safe='/')}"
        )
