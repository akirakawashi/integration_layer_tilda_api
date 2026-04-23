import re
from urllib.parse import urlparse

GOOGLE_DRIVE_HOSTS = {"drive.google.com", "www.drive.google.com"}


def extract_google_drive_file_id(file_url: str) -> str | None:
    parsed_url = urlparse(file_url)
    if parsed_url.netloc not in GOOGLE_DRIVE_HOSTS:
        return None

    path_match = re.search(r"/file/d/([^/]+)", parsed_url.path)
    if path_match is not None:
        return path_match.group(1)

    query_match = re.search(r"(?:^|[?&])id=([^&]+)", file_url)
    if query_match is not None:
        return query_match.group(1)

    return None


def build_google_drive_download_url(file_id: str) -> str:
    return f"https://drive.usercontent.google.com/u/0/uc?id={file_id}&export=download"
