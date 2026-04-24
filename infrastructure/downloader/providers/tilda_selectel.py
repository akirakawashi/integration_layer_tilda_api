import re
from html import unescape
from pathlib import Path
from urllib.parse import unquote, urlparse

TILDA_STORAGE_PAGE_HOSTS = {"tupwidget.com", "www.tupwidget.com"}
SELECTEL_STORAGE_HOSTS = {"selstorage.ru", "www.selstorage.ru"}

ANCHOR_LINK_PATTERN = re.compile(
    r"""<a\b[^>]*\bhref\s*=\s*(['"])(.*?)\1[^>]*>(.*?)</a>""",
    flags=re.IGNORECASE | re.DOTALL,
)


def is_tilda_storage_page_url(file_url: str) -> bool:
    return urlparse(file_url).netloc.lower() in TILDA_STORAGE_PAGE_HOSTS


def is_selectel_storage_url(file_url: str) -> bool:
    host = urlparse(file_url).netloc.lower()
    return host in SELECTEL_STORAGE_HOSTS or host.endswith(".selstorage.ru")


def extract_tilda_selectel_storage_link(html_text: str) -> tuple[str | None, str | None]:
    first_link: tuple[str, str | None] | None = None

    for match in ANCHOR_LINK_PATTERN.finditer(html_text):
        storage_url = unescape(match.group(2).strip())
        storage_file_name = re.sub(r"<[^>]+>", "", match.group(3)).strip() or None

        if first_link is None:
            first_link = (storage_url, storage_file_name)

        if is_selectel_storage_url(storage_url):
            return storage_url, storage_file_name

    if first_link is None:
        return None, None

    return first_link


def get_tilda_storage_page_fallback_file_name(file_url: str) -> str:
    parsed_url = urlparse(file_url)
    return Path(unquote(parsed_url.path)).name or "downloaded_file"
