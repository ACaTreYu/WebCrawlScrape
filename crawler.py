"""
WebCrawlScrape - Core Crawler Module
A minimal CLI web crawler that downloads files from a given domain.
"""

import os
import re
import time
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from collections import deque

from config import (
    DEFAULT_DOWNLOAD_DIR,
    DEFAULT_EXTENSIONS,
    DEFAULT_MAX_PAGES,
    DEFAULT_TIMEOUT,
)


# -----------------------------
# ROBOTS.TXT HANDLER
# -----------------------------
class RobotsChecker:
    """Handles robots.txt parsing and URL checking."""

    def __init__(self, base_url, user_agent="WebCrawlScrape/1.0"):
        self.user_agent = user_agent
        self.parser = RobotFileParser()
        self.loaded = False

        # Build robots.txt URL
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        try:
            self.parser.set_url(robots_url)
            self.parser.read()
            self.loaded = True
            print(f"[ROBOTS] Loaded {robots_url}")
        except Exception as e:
            print(f"[ROBOTS] Could not load robots.txt: {e}")
            self.loaded = False

    def can_fetch(self, url):
        """Check if URL is allowed by robots.txt."""
        if not self.loaded:
            return True  # Allow if robots.txt not available
        return self.parser.can_fetch(self.user_agent, url)


# -----------------------------
# DUPLICATE DETECTOR
# -----------------------------
class DuplicateDetector:
    """Detects duplicate files using hash comparison."""

    def __init__(self):
        self.hashes = set()

    def is_duplicate(self, content):
        """Check if content hash already exists."""
        file_hash = hashlib.md5(content).hexdigest()
        if file_hash in self.hashes:
            return True
        self.hashes.add(file_hash)
        return False

    def get_count(self):
        """Return number of unique files seen."""
        return len(self.hashes)


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


def get_url_depth(url, base_url):
    """Calculate the depth of a URL relative to base URL."""
    base_path = urlparse(base_url).path.rstrip('/')
    url_path = urlparse(url).path.rstrip('/')

    # Remove base path from URL path
    if url_path.startswith(base_path):
        relative_path = url_path[len(base_path):]
    else:
        relative_path = url_path

    # Count path segments
    segments = [s for s in relative_path.split('/') if s]
    return len(segments)


def download_file(url, download_dir, timeout, duplicate_detector=None):
    """
    Download a file from URL to the specified directory.
    Skips if file already exists or is a duplicate.
    """
    os.makedirs(download_dir, exist_ok=True)

    filename = os.path.basename(urlparse(url).path)
    if not filename:
        return False, "no_filename"

    path = os.path.join(download_dir, filename)

    if os.path.exists(path):
        print(f"[SKIP] {filename} (exists)")
        return False, "exists"

    try:
        r = requests.get(url, timeout=timeout, stream=True)
        r.raise_for_status()

        # Read content for duplicate check
        content = r.content

        # Check for duplicates
        if duplicate_detector and duplicate_detector.is_duplicate(content):
            print(f"[SKIP] {filename} (duplicate content)")
            return False, "duplicate"

        with open(path, "wb") as f:
            f.write(content)

        print(f"[DOWNLOADED] {filename}")
        return True, "success"

    except Exception as e:
        print(f"[ERROR] {url} -> {e}")
        return False, "error"


# -----------------------------
# CRAWLER
# -----------------------------
def crawl(
    start_url,
    allowed_exts=None,
    out_dir=None,
    max_pages=None,
    timeout=None,
    max_depth=None,
    delay=0,
    respect_robots=False,
    detect_duplicates=True,
    save_pages=False
):
    """
    Crawl starting from a URL, downloading files with matching extensions.

    Args:
        start_url: The URL to start crawling from
        allowed_exts: Set of extensions to download (e.g., {".zip", ".png"})
                      Empty set or None = download all files with extensions
        out_dir: Output directory for downloads
        max_pages: Maximum number of pages to crawl
        timeout: Request timeout in seconds
        max_depth: Maximum depth to crawl (None = unlimited)
        delay: Delay between requests in seconds (rate limiting)
        respect_robots: Whether to respect robots.txt
        detect_duplicates: Whether to skip duplicate files by hash
        save_pages: Whether to save crawled webpages to html/ subfolder

    Returns:
        dict with stats: pages_crawled, files_downloaded, errors, duplicates_skipped
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
    # Queue stores (url, depth) tuples
    queue = deque([(start_url, 0)])
    base_netloc = urlparse(start_url).netloc

    stats = {
        "pages_crawled": 0,
        "files_downloaded": 0,
        "pages_saved": 0,
        "errors": 0,
        "duplicates_skipped": 0,
        "robots_blocked": 0
    }

    # Initialize robots.txt checker
    robots = None
    if respect_robots:
        robots = RobotsChecker(start_url)

    # Initialize duplicate detector
    dup_detector = DuplicateDetector() if detect_duplicates else None

    # Create html subfolder if saving pages
    html_dir = None
    if save_pages:
        html_dir = os.path.join(out_dir, "html")
        os.makedirs(html_dir, exist_ok=True)

    while queue and stats["pages_crawled"] < max_pages:
        url, depth = queue.popleft()

        if url in visited:
            continue

        # Check max depth
        if max_depth is not None and depth > max_depth:
            continue

        # Check robots.txt
        if robots and not robots.can_fetch(url):
            print(f"[ROBOTS] Blocked: {url}")
            stats["robots_blocked"] += 1
            continue

        visited.add(url)
        stats["pages_crawled"] += 1

        depth_str = f" (depth {depth})" if max_depth is not None else ""
        print(f"[PAGE {stats['pages_crawled']}/{max_pages}]{depth_str} {url}")

        # Rate limiting
        if delay > 0 and stats["pages_crawled"] > 1:
            time.sleep(delay)

        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
        except Exception as e:
            print(f"[ERROR] {url} -> {e}")
            stats["errors"] += 1
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        # Save webpage if enabled
        if html_dir:
            try:
                # Generate filename from URL path
                parsed_url = urlparse(url)
                page_path = parsed_url.path.strip('/') or 'index'
                # Clean filename
                page_filename = re.sub(r'[<>:"/\\|?*]', '_', page_path)
                if not page_filename.endswith(('.html', '.htm')):
                    page_filename += '.html'

                page_filepath = os.path.join(html_dir, page_filename)

                # Avoid overwriting
                if not os.path.exists(page_filepath):
                    with open(page_filepath, 'w', encoding='utf-8') as f:
                        f.write(r.text)
                    print(f"[SAVED] {page_filename}")
                    stats["pages_saved"] += 1
            except Exception as e:
                print(f"[SAVE ERROR] {url} -> {e}")

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
                new_depth = depth + 1
                if max_depth is None or new_depth <= max_depth:
                    queue.append((link, new_depth))

        # Check img tags for images
        for img in soup.find_all("img", src=True):
            link = urljoin(url, img["src"])
            ext = get_extension(link)
            if ext and (not allowed_exts or ext in allowed_exts):
                file_urls.add(link)

        # Download collected files
        for file_url in file_urls:
            # Rate limiting for downloads too
            if delay > 0:
                time.sleep(delay / 2)  # Half delay for files

            success, reason = download_file(file_url, out_dir, timeout, dup_detector)
            if success:
                stats["files_downloaded"] += 1
            elif reason == "duplicate":
                stats["duplicates_skipped"] += 1

    # Summary
    print(f"\n[DONE] Pages: {stats['pages_crawled']}, "
          f"Downloaded: {stats['files_downloaded']}, "
          f"Errors: {stats['errors']}", end="")

    if save_pages:
        print(f", HTML saved: {stats['pages_saved']}", end="")
    if detect_duplicates:
        print(f", Duplicates skipped: {stats['duplicates_skipped']}", end="")
    if respect_robots:
        print(f", Robots blocked: {stats['robots_blocked']}", end="")
    print()

    return stats


# -----------------------------
# RUN (standalone)
# -----------------------------
if __name__ == "__main__":
    # Example usage - edit these values
    START_URL = "https://example.com"
    ALLOWED_EXTENSIONS = {".zip", ".png", ".jpg", ".pdf"}

    crawl(
        START_URL,
        ALLOWED_EXTENSIONS,
        max_depth=3,
        delay=0.5,
        respect_robots=True,
        detect_duplicates=True
    )
