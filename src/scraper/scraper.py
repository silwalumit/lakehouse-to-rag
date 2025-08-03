"""
Web Scraper Module

A robust web scraper that supports both single-page scraping and site crawling.
Features include rate limiting, robots.txt compliance, error handling, and MinIO integration.
"""

import concurrent
import concurrent.futures
import json
import logging
import random
import time
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from config.settings import Settings
from helpers.minio_service import MinioIOService
from scraper.config import ScraperConfig
from scraper.request import RetryingSession

# Configure logging
logger = logging.getLogger(__name__)


class Scraper:
    """
    A robust web scraper with crawling capabilities.

    Features:
    - Rate limiting to be respectful to servers
    - Robots.txt compliance
    - Retry logic for failed requests
    - MinIO integration for data storage
    - Comprehensive error handling
    - Logging for monitoring and debugging
    """

    def __init__(
        self,
        settings: Settings,
        config: Optional[ScraperConfig] = None,
        session: Optional[RetryingSession] = None,
        obj_store: Optional[MinioIOService] = None,
    ):
        """
        Initialize the scraper.

        Args:
            config: Scraper configuration. If None, uses default settings.
        """
        self.config = config or ScraperConfig()
        self.visited: Set[str] = set()
        self.session = session or RetryingSession(
            max_retries=self.config.max_retries,
            user_agent=self.config.user_agent,
        )
        secret_key = (
            settings.minio.secret_key.get_secret_value()
            if settings.minio.secret_key
            else None
        )
        self.obj_store = obj_store or MinioIOService(
            endpoint=settings.minio.connect_uri,
            access_key=settings.minio.access_key,
            secret_key=secret_key,
        )
        self.robots_parser: Optional[RobotFileParser] = None

    def _can_crawl(self, url: str) -> bool:
        """
        Check if scraping is allowed according to robots.txt.

        Args:
            url: The URL to check

        Returns:
            True if scraping is allowed, False otherwise
        """
        if not self.config.respect_robots:
            return True

        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

            if self.robots_parser is None:
                self.robots_parser = RobotFileParser()
                self.robots_parser.set_url(robots_url)
                self.robots_parser.read()

            return self.robots_parser.can_fetch(self.config.user_agent, url)

        except Exception as e:
            logger.warning(f"Could not check robots.txt for {url}: {e}")
            return True  # Allow scraping if robots.txt check fails

    def _sanitize_url(self, url: str) -> str:
        """
        Sanitize URL for use as filename.

        Args:
            url: The URL to sanitize

        Returns:
            Sanitized string safe for use as filename
        """
        return (
            url.replace("://", "_")
            .replace("/", "_")
            .replace("?", "_")
            .replace("&", "_")
        )

    def _extract_content(
        self, soup: BeautifulSoup, selectors: Dict[str, str]
    ) -> Dict[str, Optional[str]]:
        """
        Extract content from BeautifulSoup object using CSS selectors.

        Args:
            soup: BeautifulSoup object
            selectors: Dictionary of {key: css_selector} pairs

        Returns:
            Dictionary of extracted content
        """
        data = {}
        for key, selector in selectors.items():
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    # Filter out very short content
                    if len(text) >= self.config.min_content_length:
                        data[key] = text
                    else:
                        data[key] = None
                        logger.debug(
                            f"Content for '{key}' too short: {len(text)} chars"
                        )
                else:
                    data[key] = None
                    logger.debug(f"No element found for selector '{selector}'")
            except Exception as e:
                logger.warning(f"Error extracting content for '{key}': {e}")
                data[key] = None

        return data

    def _save_to_object_store(
        self,
        url: str,
        html_content: str,
        extracted_data: Dict[str, Optional[str]],
    ) -> None:
        """
        Save scraped data to MinIO.

        Args:
            url: The source URL
            html_content: Raw HTML content
            extracted_data: Extracted content dictionary
        """
        try:
            sanitized_url = self._sanitize_url(url)
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(
                        self.obj_store.upload,
                        "raw",
                        f"{sanitized_url}.html",
                        html_content,
                        content_type="text/html",
                    ),
                    executor.submit(
                        self.obj_store.upload,
                        "raw",
                        f"{sanitized_url}.json",
                        json.dumps(extracted_data, indent=2),
                        content_type="application/json",
                    ),
                ]
                concurrent.futures.wait(futures)
                logger.info("Save html and json file to bucket `raw` ")

        except Exception as e:
            logger.error(f"Failed to save data for {url}: {e}")

    def crawl_site(
        self,
        start_url: str,
        selectors: Dict[str, str],
    ) -> None:
        """
        Crawl a website and scrape all internal pages.

        Args:
            start_url: The starting URL for crawling
            selectors: Dictionary of {key: css_selector} pairs
        """

        logger.info(
            f"Starting crawl of {start_url} (max {self.config.max_pages} pages)"
        )

        to_visit = [start_url]
        domain = urlparse(start_url).netloc
        pages_scraped = 0

        while to_visit and pages_scraped < self.config.max_pages:
            url = to_visit.pop(0)

            # Skip if already visited
            if url in self.visited:
                continue

            # Randomize throtlling to resemlbe human browsing patterns
            if pages_scraped > 0 and self.config.rate_limit:
                sleep_for = random.random()
                logger.info(f"Sleeping for {sleep_for}")
                time.sleep(sleep_for)

            try:
                # Check robots.txt
                if not self._can_crawl(url):
                    logger.warning(f"Skipping {url} (not allowed by robots.txt)")
                    continue

                # Make request
                response = self.session.get(url, timeout=self.config.timeout)

                # Parse HTML
                soup = BeautifulSoup(response.text, "html.parser")

                # Extract content
                data = self._extract_content(soup, selectors)

                # Create metadata
                metadata = {
                    "url": url,
                    "scraped_at": time.time(),
                    "status_code": response.status_code,
                    "content_length": len(response.content),
                    **data,
                }

                # Save to object store
                self._save_to_object_store(url, response.text, metadata)

                # Mark as visited
                self.visited.add(url.rstrip("/"))
                pages_scraped += 1

                logger.info(f"Crawled {url} ({pages_scraped}/{self.config.max_pages})")

                # Find new internal links
                new_links = self._extract_internal_links(soup, url, domain)

                for link in new_links:
                    if link.rstrip("/") not in self.visited and link not in to_visit:
                        to_visit.append(link)

            except requests.RequestException as e:
                logger.error(f"Request failed for {url}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error crawling {url}: {e}")

        logger.info(f"Crawl completed. Visited {pages_scraped} pages.")

    def _extract_internal_links(
        self,
        soup: BeautifulSoup,
        current_url: str,
        domain: str,
    ) -> List[str]:
        """
        Extract internal links from a page.

        Args:
            soup: BeautifulSoup object
            current_url: The current page URL
            domain: The domain to restrict links to

        Returns:
            List of internal URLs
        """
        links = []

        for link in soup.find_all("a", href=True):
            href = link["href"]

            # Skip empty, javascript, mailto, etc.
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            try:
                # Resolve relative URLs
                absolute_url = urljoin(current_url, href)

                # Check if it's an internal link
                if urlparse(absolute_url).netloc == domain:
                    links.append(absolute_url)

            except Exception as e:
                logger.debug(f"Could not process link {href}: {e}")

        return links
