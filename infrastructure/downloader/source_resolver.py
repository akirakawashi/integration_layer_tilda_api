from loguru import logger

from infrastructure.downloader.content_validator import raise_for_html_document, summarize_html
from infrastructure.downloader.providers import (
    build_google_drive_download_url,
    extract_google_drive_file_id,
    extract_tupwidget_storage_link,
    get_tupwidget_fallback_file_name,
    is_tupwidget_url,
)
from infrastructure.downloader.request_utils import fetch_text_response


def resolve_download_source(
    file_url: str,
    *,
    timeout_seconds: int,
) -> tuple[str, str | None]:
    google_drive_file_id = extract_google_drive_file_id(file_url)
    if google_drive_file_id is not None:
        resolved_url = build_google_drive_download_url(google_drive_file_id)
        logger.info(
            "Resolved Google Drive file link: original_url={}, file_id={}, resolved_url={}",
            file_url,
            google_drive_file_id,
            resolved_url,
        )
        return resolved_url, None

    if not is_tupwidget_url(file_url):
        return file_url, None

    logger.info("Resolving Tilda storage page: tupwidget_url={}", file_url)
    html_text = fetch_text_response(file_url, timeout_seconds=timeout_seconds)
    storage_url, storage_file_name = extract_tupwidget_storage_link(html_text)
    if storage_url is None:
        logger.warning(
            "Could not extract storage link from Tilda page: tupwidget_url={}, html_preview={}",
            file_url,
            summarize_html(html_text),
        )
        raise_for_html_document(
            html_text=html_text,
            file_name=get_tupwidget_fallback_file_name(file_url),
        )

    logger.info(
        "Resolved Tilda storage link: tupwidget_url={}, storage_url={}, storage_file_name={}",
        file_url,
        storage_url,
        storage_file_name,
    )
    resolved_url, resolved_file_name = resolve_download_source(
        storage_url,
        timeout_seconds=timeout_seconds,
    )
    return resolved_url, storage_file_name or resolved_file_name
