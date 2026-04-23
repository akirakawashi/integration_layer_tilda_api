from urllib.parse import urlparse
from urllib.request import Request, urlopen

from loguru import logger

from exceptions import UnsupportedFileUrlSchemeError


def build_request(file_url: str) -> Request:
    parsed_url = urlparse(file_url)
    if parsed_url.scheme not in {"http", "https"}:
        raise UnsupportedFileUrlSchemeError()

    return Request(
        file_url,
        headers={
            "User-Agent": "tilda-api-file-downloader/1.0",
        },
    )


def fetch_text_response(file_url: str, *, timeout_seconds: int) -> str:
    request = build_request(file_url)
    with urlopen(request, timeout=timeout_seconds) as response:
        final_url = getattr(response, "geturl", lambda: file_url)()
        logger.info(
            "Fetched text response: request_url={}, final_url={}, content_type={}",
            file_url,
            final_url,
            response.headers.get_content_type(),
        )
        body = response.read()
    return body.decode("utf-8", errors="ignore")
