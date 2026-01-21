✅ Phase 1 — Minimal CLI Web Crawler (Python)
✅ Features

Crawl starting from one URL

Only same-domain links

Collect file links by extension

Download files

Avoid infinite loops

🔧 1. Install deps

On Windows or Linux:

pip install requests beautifulsoup4 urllib3


(urllib is built into Python)

📁 2. File: crawler.py
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque

# -----------------------------
# CONFIG
# -----------------------------
START_URL = "https://example.com"
DOWNLOAD_DIR = "downloads"
ALLOWED_EXTENSIONS = {".zip", ".png", ".jpg", ".pdf"}  # empty set = allow all
MAX_PAGES = 200


# -----------------------------
# HELPERS
# -----------------------------
def is_same_domain(url, base_netloc):
    return urlparse(url).netloc == base_netloc


def get_extension(url):
    path = urlparse(url).path
    return os.path.splitext(path)[1].lower()


def download_file(url):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    filename = os.path.basename(urlparse(url).path)
    if not filename:
        return

    path = os.path.join(DOWNLOAD_DIR, filename)

    if os.path.exists(path):
        print(f"[SKIP] {filename}")
        return

    try:
        r = requests.get(url, timeout=15, stream=True)
        r.raise_for_status()

        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"[DOWNLOADED] {filename}")

    except Exception as e:
        print(f"[ERROR] {url} -> {e}")


# -----------------------------
# CRAWLER
# -----------------------------
def crawl(start_url):
    visited = set()
    queue = deque([start_url])

    base_netloc = urlparse(start_url).netloc
    pages = 0

    while queue and pages < MAX_PAGES:
        url = queue.popleft()

        if url in visited:
            continue

        visited.add(url)
        pages += 1

        print(f"[PAGE] {url}")

        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
        except Exception as e:
            print(f"[ERROR] {url} -> {e}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        for tag in soup.find_all("a", href=True):
            link = urljoin(url, tag["href"])
            link = link.split("#")[0]

            ext = get_extension(link)

            # file?
            if ext and (not ALLOWED_EXTENSIONS or ext in ALLOWED_EXTENSIONS):
                download_file(link)
                continue

            # page?
            if is_same_domain(link, base_netloc):
                if link not in visited:
                    queue.append(link)


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    crawl(START_URL)

▶️ 3. Run It

Edit:

START_URL = "https://somesite.com"
ALLOWED_EXTENSIONS = {".zip", ".map", ".rec"}   # for ARC-style scraping later 😉


Then:

python crawler.py


Downloads go into:

./downloads/

✅ Phase 2 — Make It Configurable (for GUI Later)

Next step (still CLI):

Paste URLs

Select file types

Output folder chooser

We refactor into callable functions:

def crawl(start_url, allowed_exts, out_dir, max_pages=200):
    ...


So GUI can later just call:

crawl(url, {".zip", ".png"}, "C:/Scrapes/site1")

✅ Phase 3 — GUI Options (when ready)

Two good routes:

🟢 Simple / Fast

Tkinter

URL entry box

Checkbox list of extensions

Start button

Progress log

🔵 More Power

PyQt / PySide

Table of found files

Select before download

Multiple start URLs

⚠️ Important Safety / Legal Notes (brief but real)

Crawler currently:

Obeys same-domain only

Does NOT check robots.txt yet

Later we can add:

robots.txt parsing

rate limiting (sleep)

max depth

🔥 Where This Fits Your Bigger Picture (ARC Tools)

Jacob, this crawler is actually perfect for:

Auto-grabbing:

old ARC map packs

graphics patches

league screenshots

abandoned FTP mirrors

Later upgrades could include:

Hash checking for duplicates

Rename by detected file type

Auto-sort into:

maps/
gfx/
replays/
docs/


