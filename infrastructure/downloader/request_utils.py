from urllib.parse import quote, urlparse, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from loguru import logger

from exceptions import UnsupportedFileUrlSchemeError

PATH_SAFE_CHARS = "/:@!$&'()*+,;=%"
QUERY_SAFE_CHARS = "/?:@!$'()*+,;=%&="


def normalize_http_url(file_url: str) -> str:
    parsed_url = urlsplit(file_url.strip())

    normalized_path = quote(parsed_url.path, safe=PATH_SAFE_CHARS)
    normalized_query = quote(parsed_url.query, safe=QUERY_SAFE_CHARS)
    normalized_fragment = quote(parsed_url.fragment, safe=QUERY_SAFE_CHARS)

    return urlunsplit(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            normalized_path,
            normalized_query,
            normalized_fragment,
        )
    )


def build_request(file_url: str) -> Request:
    normalized_url = normalize_http_url(file_url)
    parsed_url = urlparse(normalized_url)
    if parsed_url.scheme not in {"http", "https"}:
        raise UnsupportedFileUrlSchemeError()

    return Request(
        normalized_url,
        headers={
            "User-Agent": "tilda-api-file-downloader/1.0",
        },
    )


def fetch_text_response(file_url: str, *, timeout_seconds: int) -> str:
    request = build_request(file_url)
    with urlopen(request, timeout=timeout_seconds) as response:
        final_url = getattr(response, "geturl", lambda: file_url)()
        logger.debug(
            "Fetched text response: request_url={}, final_url={}, content_type={}",
            file_url,
            final_url,
            response.headers.get_content_type(),
        )
        body = response.read()
    return body.decode("utf-8", errors="ignore")
