import base64
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from loguru import logger

from exceptions import (
    NextcloudAuthenticationFailedError,
    NextcloudDirectoryCreateFailedError,
    NextcloudUploadFailedError,
)
from infrastructure.uploader.path_utils import build_webdav_url


def build_auth_headers(username: str, app_password: str) -> dict[str, str]:
    credentials = f"{username}:{app_password}".encode("utf-8")
    auth_token = base64.b64encode(credentials).decode("ascii")
    return {"Authorization": f"Basic {auth_token}"}


def ensure_remote_dir(
    *,
    base_url: str,
    dav_user_id: str,
    username: str,
    app_password: str,
    remote_dir: str,
    timeout_seconds: int,
) -> None:
    if not remote_dir:
        return

    logger.debug("Ensuring Nextcloud directory exists: {}", remote_dir)
    current_parts: list[str] = []
    for part in remote_dir.split("/"):
        if not part:
            continue

        current_parts.append(part)
        directory_path = "/".join(current_parts)
        request = Request(
            build_webdav_url(
                base_url=base_url,
                dav_user_id=dav_user_id,
                remote_path=directory_path,
            ),
            headers=build_auth_headers(username, app_password),
            method="MKCOL",
        )

        try:
            with urlopen(request, timeout=timeout_seconds) as response:
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
                "Nextcloud directory creation failed with transport error: directory={}, error_type={}, error_message={}",
                directory_path,
                type(exc).__name__,
                str(exc),
            )
            raise NextcloudDirectoryCreateFailedError() from exc


def upload_file(
    *,
    base_url: str,
    dav_user_id: str,
    username: str,
    app_password: str,
    file_path: Path,
    remote_file_path: str,
    content_type: str | None,
    timeout_seconds: int,
) -> None:
    headers = build_auth_headers(username, app_password)
    headers["Content-Type"] = content_type or "application/octet-stream"

    request = Request(
        build_webdav_url(
            base_url=base_url,
            dav_user_id=dav_user_id,
            remote_path=remote_file_path,
        ),
        data=file_path.read_bytes(),
        headers=headers,
        method="PUT",
    )

    try:
        logger.debug("Uploading file to Nextcloud path: {}", remote_file_path)
        with urlopen(request, timeout=timeout_seconds) as response:
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
            "Nextcloud upload failed with transport error: remote_file_path={}, error_type={}, error_message={}",
            remote_file_path,
            type(exc).__name__,
            str(exc),
        )
        raise NextcloudUploadFailedError() from exc
