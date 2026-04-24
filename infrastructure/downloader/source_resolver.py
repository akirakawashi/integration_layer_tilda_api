from loguru import logger

from infrastructure.downloader.content_validator import raise_for_html_document, summarize_html
from infrastructure.downloader.providers import (
    extract_tilda_selectel_storage_link,
    get_tilda_storage_page_fallback_file_name,
    is_selectel_storage_url,
    is_tilda_storage_page_url,
)
from infrastructure.downloader.request_utils import fetch_text_response


def resolve_download_source(
    file_url: str,
    *,
    timeout_seconds: int,
) -> tuple[str, str | None]:
    if is_selectel_storage_url(file_url):
        return file_url, None

    if not is_tilda_storage_page_url(file_url):
        return file_url, None

    logger.debug("Resolving Tilda storage page to direct Selectel link: landing_url={}", file_url)
    html_text = fetch_text_response(file_url, timeout_seconds=timeout_seconds)
    storage_url, storage_file_name = extract_tilda_selectel_storage_link(html_text)
    if storage_url is None:
        logger.debug(
            "Could not extract direct Selectel link from Tilda storage page: landing_url={}, html_preview={}",
            file_url,
            summarize_html(html_text),
        )
        raise_for_html_document(
            html_text=html_text,
            file_name=get_tilda_storage_page_fallback_file_name(file_url),
        )

    logger.debug(
        (
            "Resolved direct Selectel download link from Tilda page: "
            "landing_url={}, storage_url={}, storage_file_name={}"
        ),
        file_url,
        storage_url,
        storage_file_name,
    )
    resolved_url, resolved_file_name = resolve_download_source(
        storage_url,
        timeout_seconds=timeout_seconds,
    )
    return resolved_url, storage_file_name or resolved_file_name
