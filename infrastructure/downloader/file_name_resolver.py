from pathlib import Path
from urllib.parse import unquote, urlparse


def resolve_file_name(
    response,
    original_url: str,
    *,
    suggested_file_name: str | None = None,
) -> str:
    header_file_name = response.headers.get_filename()
    if header_file_name:
        return Path(unquote(header_file_name)).name

    if suggested_file_name:
        return Path(unquote(suggested_file_name)).name

    final_url = getattr(response, "geturl", lambda: original_url)()
    final_file_name = Path(unquote(urlparse(final_url).path)).name
    if final_file_name:
        return final_file_name

    original_file_name = Path(unquote(urlparse(original_url).path)).name
    if original_file_name:
        return original_file_name

    return "downloaded_file"
