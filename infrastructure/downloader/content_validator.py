import re
import zipfile
from pathlib import Path
from typing import NoReturn

from loguru import logger

from exceptions import (
    DownloadedFileContentMismatchError,
    DownloadedFileNotReadyError,
    DownloadedFileSignatureMismatchError,
)

RAR4_SIGNATURE = b"Rar!\x1a\x07\x00"
RAR5_SIGNATURE = b"Rar!\x1a\x07\x01\x00"


def validate_downloaded_content(
    *,
    file_path: Path,
    file_name: str,
    content_type: str | None,
) -> None:
    with file_path.open("rb") as file:
        prefix = file.read(4096)

    stripped_prefix = prefix.lstrip()
    lower_prefix = stripped_prefix.lower()
    is_html = (
        lower_prefix.startswith(b"<!doctype html")
        or lower_prefix.startswith(b"<html")
        or (content_type == "text/html" and b"<html" in lower_prefix)
    )
    if is_html:
        html_text = stripped_prefix.decode("utf-8", errors="ignore").lower()
        logger.warning(
            "Downloaded HTML instead of file: file_name={}, content_type={}, html_preview={}",
            file_name,
            content_type,
            summarize_html(html_text),
        )
        raise_for_html_document(html_text=html_text, file_name=file_name)

    validate_archive_signature(
        file_path=file_path,
        file_name=file_name,
        prefix=prefix,
    )


def raise_for_html_document(
    *,
    html_text: str,
    file_name: str,
) -> NoReturn:
    if (
        "tilda: go to storage" in html_text
        or "has not been uploaded to the file storage service yet" in html_text
        or "try in 5 minutes" in html_text
    ):
        logger.warning(
            "Tilda storage reports file is not ready yet: file_name={}, html_preview={}",
            file_name,
            summarize_html(html_text),
        )
        raise DownloadedFileNotReadyError(file_name)

    logger.warning(
        "Remote server returned unexpected HTML page instead of file: file_name={}, html_preview={}",
        file_name,
        summarize_html(html_text),
    )
    raise DownloadedFileContentMismatchError(file_name)


def validate_archive_signature(
    *,
    file_path: Path,
    file_name: str,
    prefix: bytes,
) -> None:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".zip":
        if zipfile.is_zipfile(file_path):
            return
        logger.warning(
            "Downloaded file failed ZIP signature check: file_name={}, prefix_hex={}",
            file_name,
            prefix[:16].hex(),
        )
        raise DownloadedFileSignatureMismatchError(file_name, "zip")

    if suffix == ".rar":
        if prefix.startswith((RAR4_SIGNATURE, RAR5_SIGNATURE)):
            return
        logger.warning(
            "Downloaded file failed RAR signature check: file_name={}, prefix_hex={}",
            file_name,
            prefix[:16].hex(),
        )
        raise DownloadedFileSignatureMismatchError(file_name, "rar")


def summarize_html(html_text: str) -> str:
    compact = re.sub(r"\s+", " ", html_text).strip()
    return compact[:240]
