import asyncio
from dataclasses import dataclass
import logging
from datetime import datetime
from typing import Generator

from django.utils import timezone
import requests
from bs4 import BeautifulSoup

from django.core.validators import URLValidator
from urllib.parse import urlparse

import urllib3
urllib3.disable_warnings()
logger = logging.getLogger(__name__)


from commons.async_retry import (
    retry,
    RetryPolicyStrategy,
    RetryInfo
)

# This example shows the usage with python typings
def retry_policy(info: RetryInfo) -> RetryPolicyStrategy:
    """
    - It will always retry until succeeded
    - If fails for the first time, it will retry immediately,
    - If it fails again,
      aioretry will perform a 100ms delay before the second retry,
      200ms delay before the 3rd retry,
      the 4th retry immediately,
      100ms delay before the 5th retry,
      etc...
    """
    if info.fails >= 3:
        return True, 0
    return False, (info.fails - 1) % 3 * 0.1


@dataclass
class InternalLink:
    """
    Represents an internal link found in a webpage.

    Kwargs for initialization:
    -------------------------
      from_page (str): The URL of the page where the link was found.
      to_page (str): The URL of the page the link points to.
      anchor_text (str): The anchor text of the link.
    """
    from_page: str
    to_page: str
    anchor_text: str = ""


@dataclass
class Page:
    """
    Represents a webpage discovered by a Crawler.
    """

    url: str
    page_depth: int
    meta_title: str
    meta_description: str

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
        self.internal_links = []
        self.pages = set()

    @staticmethod
    def _extract_values_from_page(html: str) -> Page:
        pass

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
        for url, html in pages_content:
            page = self._extract_values_from_page(html)
            self.pages.add(page)
            internal_urls.extend(self._get_internal_links(html, url))
        internal_urls = set(internal_urls)
        new_internal_urls = internal_urls - self.visited_url
        self.visited_url |= internal_urls
        print(f"Depth {self.current_depth} over: {len(new_internal_urls)} new internal links found.")
        if new_internal_urls:
            self.current_depth += 1
            self._crawl_at_current_depth(new_internal_urls)
        return

    def _get_internal_links(self, page_content: str, url: str) -> Generator:
        """Return all internal links found from a page HTML content."""
        bs = BeautifulSoup(page_content, 'html.parser')
        links = bs.findAll('a')
        for link in links:
            if not link.get('href'):
                continue
            href = link.get('href')
            if (
                href.startswith("mailto") or href.startswith("tel")
            ):
                continue
            if not href.startswith('http'):
                leading_slash = '' if href.startswith('/') else '/'
                href = self.website + leading_slash + href
            if '#' in href:
                href = href.split('#')[0]
            if href.startswith('http://' + self.domain) or href.startswith('https://' + self.domain) and not href.endswith('.pdf'):
                internal_link = self._remove_trailing_slash(href)
                self.internal_links.append(
                    InternalLink(from_page=url, to_page=internal_link, anchor_text=link.text)
                )
                yield internal_link

    def _before_retry(self, info: RetryInfo):
        """Log the retry."""
        print("retrying..." + str(info.fails) + " " + str(info.exception) + " " + str(info.since))

    @retry(retry_policy, before_retry="_before_retry")
    async def _get_page_content(self, page: str) -> tuple[str, str]:
        """Return a tuple containing: (URL of the page, its HTML content)."""
        response = await asyncio.wait_for(
            asyncio.to_thread(
                requests.get,
                page,
                headers={"User-Agent": self.user_agent},
                verify=False
            ),
            timeout=self.timeout
        )
        return page, response.text


    def _get_pages_content(self, pages: list[str], loop: asyncio.AbstractEventLoop = None) -> list[str]:
        """Return the content of a list of pages by batch of 'max_concurrent_requests'."""
        contents = []
        for i in range(0, len(pages), self.max_concurrent_requests):
            print(f"Getting content of pages {i} to {i + self.max_concurrent_requests}.")
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
