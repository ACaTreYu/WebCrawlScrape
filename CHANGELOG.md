# Changelog

All notable changes to WebCrawlScrape will be documented in this file.

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
