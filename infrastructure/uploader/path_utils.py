import posixpath
import uuid
from pathlib import Path
from urllib.parse import quote


def build_stored_file_name(file_name: str) -> str:
    suffix = Path(file_name).suffix.lower()
    return f"{uuid.uuid4().hex}{suffix}"


def normalize_remote_dir(remote_dir: str) -> str:
    normalized = posixpath.normpath(remote_dir.strip("/"))
    return "" if normalized == "." else normalized


def quote_remote_path(remote_path: str) -> str:
    return "/".join(quote(part, safe="") for part in remote_path.split("/") if part)


def build_webdav_url(
    *,
    base_url: str,
    dav_user_id: str,
    remote_path: str,
) -> str:
    webdav_root = f"{base_url.rstrip('/')}/remote.php/dav/files/{quote(dav_user_id, safe='')}"
    quoted_path = quote_remote_path(remote_path)

    if not quoted_path:
        return webdav_root

    return f"{webdav_root}/{quoted_path}"


def build_public_url(public_base_url: str | None, remote_file_path: str) -> str | None:
    if not public_base_url:
        return None

    return f"{public_base_url.rstrip('/')}/{quote_remote_path(remote_file_path)}"
