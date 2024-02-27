from datetime import datetime
from django.utils import timezone
import requests
from functools import cache
from django.core.validators import URLValidator
from urllib.parse import urlparse


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
    """
    def __init__(
            self,
            website: str = None,
            user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            exclude_patterns: list[str] = None,
            exclude_pages: list[str] = None,
            exclude_url_params: bool = True,
            timeout: int = 8
    ):
        self.website = website
        self.user_agent = user_agent
        self.exclude_patterns = exclude_patterns or []
        self.exclude_pages = exclude_pages or []
        self.exclude_url_params = exclude_url_params
        self.timeout = timeout
        # Crawl stats
        self.start_crawl_time = None
        self.end_crawl_time = None
        self.pages = set()

    def _recursive_visit_page(self, url: str) -> Page:
        """Visit a page and return a Page object."""
        response = requests.get(url, headers={"User-Agent": self.user_agent}, timeout=self.timeout)
        page = Page(url=url, html=response.text)
        self.pages.add(page)
        internal_links = page.get_internal_links()
        for link in internal_links:
            if link not in self.pages:
                self._recursive_visit_page(link)
        return page

    def crawl(self):
        """Start crawling all the pages of the website."""
        self.validate_website()
        self.start_crawl_time = timezone.now()
        self._recursive_visit_page(self.website)
        self.end_crawl_time = timezone.now()

    def validate_website(self) -> None:
        """Make sure 'self.website' is a valid URL and is the root page of website."""
        if not self.website:
            raise ValueError("No website provided in Crawler init().")
        URLValidator()(self.website)  # raises ValidationError if not valid URL
        parsed_url = urlparse(self.website)
        # Keep only scheme and hostname (root)
        self.website = f"{parsed_url.scheme}://{parsed_url.hostname}"
