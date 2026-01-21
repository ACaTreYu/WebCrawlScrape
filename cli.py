"""
WebCrawlScrape - Command Line Interface
Usage: python cli.py <url> [options]
"""

import argparse
import sys
from config import (
    DEFAULT_DOWNLOAD_DIR,
    DEFAULT_MAX_PAGES,
    DEFAULT_TIMEOUT,
    EXTENSION_PRESETS,
    parse_extensions,
)
from crawler import crawl


def list_presets():
    """Display available extension presets."""
    print("\nAvailable extension presets:")
    print("-" * 40)
    for name, exts in EXTENSION_PRESETS.items():
        if exts:
            print(f"  {name:12} -> {', '.join(sorted(exts))}")
        else:
            print(f"  {name:12} -> (matches any file extension)")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="WebCrawlScrape - Download files from websites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py https://example.com
  python cli.py https://example.com -e .zip,.png
  python cli.py https://example.com -e images -o ./my_downloads
  python cli.py https://example.com -e archives,images -m 50
  python cli.py --presets
        """,
    )

    parser.add_argument(
        "url",
        nargs="?",
        help="Starting URL to crawl",
    )

    parser.add_argument(
        "-e", "--extensions",
        type=str,
        default="",
        help="File extensions to download. Use preset names (images, archives, arc) "
             "or comma-separated extensions (.zip,.png). Default: archives + images",
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        default=DEFAULT_DOWNLOAD_DIR,
        help=f"Output directory for downloads (default: {DEFAULT_DOWNLOAD_DIR})",
    )

    parser.add_argument(
        "-m", "--max-pages",
        type=int,
        default=DEFAULT_MAX_PAGES,
        help=f"Maximum pages to crawl (default: {DEFAULT_MAX_PAGES})",
    )

    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )

    parser.add_argument(
        "--presets",
        action="store_true",
        help="List available extension presets and exit",
    )

    args = parser.parse_args()

    # Show presets if requested
    if args.presets:
        list_presets()
        sys.exit(0)

    # URL is required unless showing presets
    if not args.url:
        parser.print_help()
        print("\nError: URL is required")
        sys.exit(1)

    # Parse extensions
    extensions = parse_extensions(args.extensions)

    # Display config
    print("=" * 50)
    print("WebCrawlScrape")
    print("=" * 50)
    print(f"URL:        {args.url}")
    print(f"Extensions: {', '.join(sorted(extensions)) if extensions else '(all)'}")
    print(f"Output:     {args.output}")
    print(f"Max pages:  {args.max_pages}")
    print(f"Timeout:    {args.timeout}s")
    print("=" * 50)
    print()

    # Run crawler
    try:
        stats = crawl(
            start_url=args.url,
            allowed_exts=extensions,
            out_dir=args.output,
            max_pages=args.max_pages,
            timeout=args.timeout,
        )
        return 0 if stats["errors"] == 0 else 1
    except KeyboardInterrupt:
        print("\n[CANCELLED] Crawl interrupted by user")
        return 130


if __name__ == "__main__":
    sys.exit(main())
