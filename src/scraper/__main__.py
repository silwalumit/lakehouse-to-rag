"""
Command-line interface for the web scraper.

Usage:
    python -m scraper --config config.yaml --crawl --max-pages 50
    python -m scraper --url https://example.com --selectors '{"title": "h1", "content": ".main"}' --crawl
"""

import argparse
import json
import logging
import sys
from typing import Dict

from src.config.settings import Settings
from src.helpers.logging.logger import setup_logger


def parse_selectors(selectors_str: str) -> Dict[str, str]:
    """Parse selectors from JSON string."""
    try:
        return json.loads(selectors_str)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid selectors JSON: {e}")
        sys.exit(1)


def main():
    """Main CLI function."""

    # load settings from .env
    settings = Settings()  # pyright: ignore[reportCallIssue]
    # configure logging
    setup_logger(settings.log)

    parser = argparse.ArgumentParser(
        description="Web scraper with crawling capabilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
            # Scrape single page with config file
            python -m scraper --config config.yaml

            # Crawl site with config file
            python -m scraper --config config.yaml --crawl --max-pages 50


            # Scrape with command line arguments
            python -m scraper --url https://example.com --selectors '{"title": "h1", "content": ".main"}'

            # Crawl with custom settings
            python -m scraper --url https://example.com --selectors '{"title": "h1"}' --crawl --rate-limit 2.0
        """,
    )

    # Configuration options, create a mutually exclusive group for config and url
    config_group = parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument("--config", type=str, help="Path to YAML config file")
    config_group.add_argument("--url", type=str, help="URL to scrape")

    # Selectors (required with --url)
    parser.add_argument(
        "--selectors",
        type=str,
        help="JSON string of CSS selectors (required with --url)",
    )

    # # Crawling options
    # parser.add_argument("--crawl", action="store_true", help="Crawl all internal links")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=100,
        help="Maximum pages to crawl (default: 100)",
    )

    # Scraper behavior options
    parser.add_argument(
        "--rate-limit",
        action="store_true",
        help="Enable rate limit",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--max-retries", type=int, default=3, help="Maximum retry attempts (default: 3)"
    )
    parser.add_argument(
        "--user-agent",
        type=str,
        default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15",
        help="User agent string",
    )
    parser.add_argument(
        "--ignore-robots", action="store_true", help="Ignore robots.txt restrictions"
    )
    parser.add_argument(
        "--min-content-length",
        type=int,
        default=50,
        help="Minimum content length to extract (default: 50)",
    )

    # Output options
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Validate arguments
    if args.url and not args.selectors:
        parser.error("--selectors is required when using --url")

    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        from src.scraper.config import ScraperConfig, load_config_from_file
        from src.scraper.scraper import Scraper

        # Load configuration
        if args.config:
            config = load_config_from_file(args.config)
            url = config["site_url"]
            selectors = config["selectors"]
            # Create scraper with configuration from file
            scraper_config = ScraperConfig.from_dict(config)
        else:
            url = args.url
            selectors = parse_selectors(args.selectors)
            # Create scraper with command line configuration
            scraper_config = ScraperConfig.from_args(args)

        # Create scraper
        scraper = Scraper(settings, scraper_config)

        # Run scraper
        logging.info(f"Starting crawl of {url} (max {scraper_config.max_pages} pages)")
        scraper.crawl_site(url, selectors)

        logging.info("Scraping completed successfully")

    except KeyboardInterrupt:
        logging.info("Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Scraping failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
