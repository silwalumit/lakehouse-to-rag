import argparse
import logging
import sys
from dataclasses import dataclass
from typing import Any, Type

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ScraperConfig:
    """Configuration class for scraper settings."""

    rate_limit: bool = True
    timeout: int = 30
    max_retries: int = 3
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15"
    respect_robots: bool = True
    max_pages: int = 100
    min_content_length: int = 50

    @classmethod
    def from_args(
        cls: Type["ScraperConfig"],
        args: argparse.Namespace,
    ) -> "ScraperConfig":
        return cls(
            rate_limit=args.rate_limit,
            timeout=args.timeout,
            max_retries=args.max_retries,
            user_agent=args.user_agent,
            respect_robots=not args.ignore_robots,
            max_pages=args.max_pages,
            min_content_length=args.min_content_length,
        )

    @classmethod
    def from_dict(
        cls: Type["ScraperConfig"],
        config: dict[str, Any],
    ) -> "ScraperConfig":
        advanced = config["advanced"]
        return cls(
            rate_limit=advanced["rate_limit"],
            timeout=advanced["timeout"],
            max_retries=advanced["max_retries"],
            user_agent=advanced["user_agent"],
            respect_robots=advanced["respect_robots"],
            max_pages=advanced["max_pages"],
            min_content_length=advanced["min_content_length"],
        )


def load_config_from_file(config_path: str) -> dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to load config from {config_path}: {e}")
        sys.exit(1)
