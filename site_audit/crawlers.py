import asyncio
import logging
from asyncio import Future
from datetime import datetime
from typing import Generator

import httpx
from django.utils import timezone
import requests
from functools import cache
from bs4 import BeautifulSoup

from django.core.validators import URLValidator
from urllib.parse import urlparse


logger = logging.getLogger(__name__)


class Page:
    """
    Represents a webpage discovered by a Crawler.
    """
    def __init__(self, url: str = None, html: str = None, crawled_at: datetime = timezone.now()):
        self.url = url
        self.html = html
        self.crawled_at = crawled_at

    def __eq__(self, other):
        """Consider two Pages are equal if their URLs are equal."""
        return self.url == other.url

    def __hash__(self):
        """Return the hash of the URL."""
        return hash(self.url)


class Crawler:
    """
    A Crawler is responsible for crawling a website and returning all the pages it finds.

    Kwargs for initialization:
    -------------------------
      website (str): The website to crawl.
      user_agent (str): The user agent to use when making requests to the website.
      exclude_patterns (list): A list of patterns (re) of pages not to crawl.
      exclude_pages (list): A list of specific pages not to crawl.
      exclude_url_params (bool): Whether to exclude URL parameters when checking if a page has already been crawled.
      timeout (int): The timeout in seconds waiting for page to load fully.
      max_concurrent_requests (int): The maximum number of concurrent requests to make to the website.
    """
    def __init__(
            self,
            website: str = None,
            user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            exclude_patterns: list[str] = None,
            exclude_pages: list[str] = None,
            exclude_url_params: bool = True,
            timeout: int = 8,
            max_concurrent_requests: int = 5
    ):
        self.website = website
        self.user_agent = user_agent
        self.exclude_patterns = exclude_patterns or []
        self.exclude_pages = exclude_pages or []
        self.exclude_url_params = exclude_url_params
        self.timeout = timeout
        self.max_concurrent_requests = max_concurrent_requests
        self.domain = ""
        # Crawl stats
        self.current_depth = 0
        self.start_crawl_time = None
        self.end_crawl_time = None
        self.visited_url = set()

    @staticmethod
    def _remove_trailing_slash(url: str) -> str:
        """Remove trailing slash from URL (if any)."""
        if url.endswith('/'):
            return url[:-1]
        return url

    def _crawl_at_current_depth(self, pages: set[str]):
        """Crawl all the pages at the current depth."""
        pages_content = self._get_pages_content(list(pages), asyncio.get_event_loop())
        internal_urls = []
        for content in pages_content:
            internal_urls.extend(self._get_internal_links(content))
        internal_urls = set(internal_urls)
        new_internal_urls = internal_urls - self.visited_url
        self.visited_url |= internal_urls
        if new_internal_urls:
            self.current_depth += 1
            self._crawl_at_current_depth(new_internal_urls)
        return

    def _get_internal_links(self, page_content: str) -> Generator:
        """Return all internal links found in a page."""
        bs = BeautifulSoup(page_content, 'html.parser')
        links = bs.findAll('a')
        for link in links:
            if not link.get('href'):
                continue
            href = link.get('href')
            if (
                href.startswith("#") or href.startswith("mailto") or href.startswith("tel")
                or href.startswith("/#")
            ):
                continue
            if not href.startswith('http'):
                leading_slash = '' if href.startswith('/') else '/'
                href = self.website + leading_slash + href
            if href.startswith(self.website + '#'):
                continue
            if href.startswith('http://' + self.domain) or href.startswith('https://' + self.domain) and not href.endswith('.pdf'):
                yield self._remove_trailing_slash(href)

    async def _get_page_content(self, page: str) -> str:
        """Return the content of a page."""
        response = await asyncio.to_thread(
            requests.get,
            page,
            headers={"User-Agent": self.user_agent},
            timeout=self.timeout,
            verify=False
        )
        return response.text

    def _get_pages_content(self, pages: list[str], loop: asyncio.AbstractEventLoop = None) -> list[str]:
        """Return the content of a list of pages by batch of 'max_concurrent_requests'."""
        contents = []
        for i in range(0, len(pages), self.max_concurrent_requests):
            coroutines = [self._get_page_content(page) for page in pages[i:i + self.max_concurrent_requests]]
            res = loop.run_until_complete(asyncio.gather(*coroutines))
            contents.extend(res)
        return contents

    def crawl(self):
        """Start crawling all the pages of the website."""
        self.validate_website()
        self.start_crawl_time = timezone.now()
        self._crawl_at_current_depth({self.website})
        self.end_crawl_time = timezone.now()
        print(f"Crawling '{self.website}' ({len(self.visited_url)} pages) done in {self.end_crawl_time - self.start_crawl_time}.")

    def validate_website(self) -> None:
        """Make sure 'self.website' is a valid URL and is the root page of website."""
        if not self.website:
            raise ValueError("No website provided in Crawler init().")
        URLValidator()(self.website)  # raises ValidationError if not valid URL
        parsed_url = urlparse(self.website)
        # Keep only scheme and hostname (root)
        self.website = f"{parsed_url.scheme}://{parsed_url.hostname}"
        self.domain = parsed_url.hostname
        self.visited_url.add(self.website)
