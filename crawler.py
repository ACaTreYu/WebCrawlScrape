"""
WebCrawlScrape - Core Crawler Module
A minimal CLI web crawler that downloads files from a given domain.
"""

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque

from config import (
    DEFAULT_DOWNLOAD_DIR,
    DEFAULT_EXTENSIONS,
    DEFAULT_MAX_PAGES,
    DEFAULT_TIMEOUT,
)


# -----------------------------
# HELPERS
# -----------------------------
def is_same_domain(url, base_netloc):
    """Check if URL belongs to the same domain."""
    return urlparse(url).netloc == base_netloc


def get_extension(url):
    """Extract lowercase file extension from URL."""
    path = urlparse(url).path
    return os.path.splitext(path)[1].lower()


def download_file(url, download_dir=DEFAULT_DOWNLOAD_DIR, timeout=DEFAULT_TIMEOUT):
    """
    Download a file from URL to the specified directory.
    Skips if file already exists.
    """
    os.makedirs(download_dir, exist_ok=True)

    filename = os.path.basename(urlparse(url).path)
    if not filename:
        return False

    path = os.path.join(download_dir, filename)

    if os.path.exists(path):
        print(f"[SKIP] {filename}")
        return False

    try:
        r = requests.get(url, timeout=timeout, stream=True)
        r.raise_for_status()

        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"[DOWNLOADED] {filename}")
        return True

    except Exception as e:
        print(f"[ERROR] {url} -> {e}")
        return False


# -----------------------------
# CRAWLER
# -----------------------------
def crawl(start_url, allowed_exts=None, out_dir=None, max_pages=None, timeout=None):
    """
    Crawl starting from a URL, downloading files with matching extensions.

    Args:
        start_url: The URL to start crawling from
        allowed_exts: Set of extensions to download (e.g., {".zip", ".png"})
                      Empty set or None = download all files with extensions
        out_dir: Output directory for downloads
        max_pages: Maximum number of pages to crawl
        timeout: Request timeout in seconds

    Returns:
        dict with stats: pages_crawled, files_downloaded, errors
    """
    # Apply defaults
    if allowed_exts is None:
        allowed_exts = DEFAULT_EXTENSIONS
    if out_dir is None:
        out_dir = DEFAULT_DOWNLOAD_DIR
    if max_pages is None:
        max_pages = DEFAULT_MAX_PAGES
    if timeout is None:
        timeout = DEFAULT_TIMEOUT

    visited = set()
    queue = deque([start_url])
    base_netloc = urlparse(start_url).netloc

    stats = {
        "pages_crawled": 0,
        "files_downloaded": 0,
        "errors": 0
    }

    while queue and stats["pages_crawled"] < max_pages:
        url = queue.popleft()

        if url in visited:
            continue

        visited.add(url)
        stats["pages_crawled"] += 1

        print(f"[PAGE {stats['pages_crawled']}/{max_pages}] {url}")

        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
        except Exception as e:
            print(f"[ERROR] {url} -> {e}")
            stats["errors"] += 1
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        # Collect all potential file URLs
        file_urls = set()

        # Check anchor tags
        for tag in soup.find_all("a", href=True):
            link = urljoin(url, tag["href"])
            link = link.split("#")[0]  # Remove fragment

            if not link or link in visited:
                continue

            ext = get_extension(link)

            # Is it a file to download?
            if ext and (not allowed_exts or ext in allowed_exts):
                file_urls.add(link)
                continue

            # Is it a page to crawl?
            if is_same_domain(link, base_netloc) and link not in visited:
                queue.append(link)

        # Check img tags for images
        for img in soup.find_all("img", src=True):
            link = urljoin(url, img["src"])
            ext = get_extension(link)
            if ext and (not allowed_exts or ext in allowed_exts):
                file_urls.add(link)

        # Download collected files
        for file_url in file_urls:
            if download_file(file_url, out_dir, timeout):
                stats["files_downloaded"] += 1

    print(f"\n[DONE] Pages: {stats['pages_crawled']}, "
          f"Downloaded: {stats['files_downloaded']}, "
          f"Errors: {stats['errors']}")

    return stats


# -----------------------------
# RUN (standalone)
# -----------------------------
if __name__ == "__main__":
    # Example usage - edit these values
    START_URL = "https://example.com"
    ALLOWED_EXTENSIONS = {".zip", ".png", ".jpg", ".pdf"}

    crawl(START_URL, ALLOWED_EXTENSIONS)
