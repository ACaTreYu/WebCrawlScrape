# Changelog

All notable changes to WebCrawlScrape will be documented in this file.

## [00.00.02] - 2026-01-21

### Added
- **Robots.txt support** - Optional respect for robots.txt rules
- **Rate limiting** - Configurable delay between requests (0-10 seconds)
- **Max depth control** - Limit crawl depth from starting URL (0 = unlimited)
- **Duplicate detection** - Skip files with identical content using MD5 hash
- **Save webpages** - Option to save crawled HTML pages to `html/` subfolder
- GUI: New options panel with all crawler settings
  - Max depth spinbox
  - Delay slider
  - Respect robots.txt checkbox
  - Skip duplicates checkbox
  - Save webpages checkbox

### Changed
- Crawler now tracks depth and respects max_depth parameter
- Download function returns status for better statistics
- Expanded crawl statistics (duplicates skipped, robots blocked, pages saved)
- Archive.org folder naming now includes URL path (e.g., `arc.won.net/guide/` -> `arcwonguide`)

### Technical
- `RobotsChecker` class for robots.txt parsing
- `DuplicateDetector` class for hash-based deduplication
- `get_url_depth()` helper function

---

## [00.00.01] - 2026-01-21

### Added
- Core crawler module with BFS traversal
- Same-domain link filtering
- Support for `<a href>` and `<img src>` tag scanning
- File download with skip-existing and streaming
- CLI interface with argparse
- Extension presets (images, archives, documents, audio, video, code, arc)
- Custom extension support
- Tkinter GUI for Windows
  - URL entry field
  - Category dropdown with checkbox-style extension filters
  - Select All / Clear All buttons for extensions
  - Custom extension input
  - Output directory picker with Browse button
  - Subfolder organization by website
  - Auto-generated folder name preview (updates as you type)
  - Max pages setting
  - Start/Stop buttons
  - Scrollable log output
  - Background threading (UI stays responsive)
- Web Archive (archive.org) URL support
  - Extracts original URL from archived snapshots
  - Generates clean folder names (e.g., `arc.won.net` -> `arcwon`)
- Version control system

### Technical
- `crawler.py` - Core crawling logic
- `config.py` - Centralized settings and presets
- `cli.py` - Command-line interface
- `gui.py` - Tkinter GUI
- `version.py` - Version management
