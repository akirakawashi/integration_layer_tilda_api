import re
from html import unescape
from pathlib import Path
from urllib.parse import unquote, urlparse

TUPWIDGET_HOSTS = {"tupwidget.com", "www.tupwidget.com"}


def is_tupwidget_url(file_url: str) -> bool:
    return urlparse(file_url).netloc in TUPWIDGET_HOSTS


def extract_tupwidget_storage_link(html_text: str) -> tuple[str | None, str | None]:
    match = re.search(
        r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match is None:
        return None, None

    storage_url = unquote(unescape(match.group(1).strip()))
    storage_file_name = re.sub(r"<[^>]+>", "", match.group(2)).strip() or None
    return storage_url, storage_file_name


def get_tupwidget_fallback_file_name(file_url: str) -> str:
    parsed_url = urlparse(file_url)
    return Path(unquote(parsed_url.path)).name or "downloaded_file"
