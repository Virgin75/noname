import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import logging

import modal

from site_audit.tasks import visit_page
from random import randint
from time import sleep

from playwright.sync_api import sync_playwright, Request, Route
from typing import Generator

from django.utils import timezone
from bs4 import BeautifulSoup

from django.core.validators import URLValidator
from urllib.parse import urlparse


@dataclass
class InternalLink:
    """
    Represents an internal link found in a webpage.

    Kwargs for initialization:
    -------------------------
      from_page (str): The URL of the page where the link was found.
      to_page (str): The URL of the page the link points to.
      anchor_text (str): The anchor text of the link.
      from_page_depth (int):  Depth of the page on which the link was found.
    """
    from_page: str
    to_page: str
    anchor_text: str = ""
    from_page_anchor_text: int = 0


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
            timeout: int = 15,
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
        # Temporary storage for JS content
        self.pages_js = {}
        # Thread pool settings
        self.thread_pool = None
        self.tls = None
        # Crawl stats
        self.current_depth = 0
        self.start_crawl_time = None
        self.end_crawl_time = None
        self.visited_url = set()
        self.internal_links = []
        self.pages = set()

    def _init_worker(self, tls):
        """Initialize the Threads local storage with a Playwright instance."""
        tls.playwright = sync_playwright().start()
        tls.current_page = {}

    @staticmethod
    def _remove_trailing_slash(url: str) -> str:
        """Remove trailing slash from URL (if any)."""
        if url.endswith('/'):
            return url[:-1]
        return url

    def _crawl_at_current_depth(self, pages: set[str]):
        """Crawl all the pages at the current depth."""
        pages_at_current_depth = list(pages)
        internal_urls_found = []
        limit = self.max_concurrent_requests
        print(f"Getting content of pages at depth {self.current_depth}...")

        while pages_at_current_depth:
            print(f"Pages left: {len(pages_at_current_depth)}")
            current_batch_urls = pages_at_current_depth[:limit]
            pages_content = []
            for res in self.thread_pool.map(self._get_page_content, current_batch_urls):
                pages_content.append(res)
            for url, html in pages_content:
                internal_urls_found.extend(self._get_internal_links(html, url))
            self.visited_url |= set(current_batch_urls)
            del pages_at_current_depth[:limit]

        new_internal_urls = set(internal_urls_found) - self.visited_url
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
                href.startswith("mailto") or href.startswith("tel") or href.startswith("javascript")
            ):
                continue
            if not href.startswith('http'):
                leading_slash = '' if href.startswith('/') else '/'
                href = self.website + leading_slash + href
            if '#' in href:
                href = href.split('#')[0]
            if href.startswith('http://' + self.domain) or href.startswith('https://' + self.domain) and not href.endswith('.pdf'):
                internal_link = self._remove_trailing_slash(href)
                yield internal_link

    def _check_resource(self, route: Route) -> None:
        """Abort requests for non-HTML/JS resources. We don't want to download them."""
        if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
            route.abort()
        elif route.request.resource_type == "script":
            exclude_list = ["analytics.js", "gtm.js", "matomo.js"]
            if any(script for script in exclude_list if script in route.request.url):
                route.abort()
            else:
                res = route.fetch()
                self.tls.current_page[threading.current_thread().name]["js"] += res.text()
                route.continue_()
        else:
            route.continue_()

    def _get_page_content(self, url: str, max_retries: int = 3) -> tuple[str, str]:
        """Return a tuple containing: (URL of the page, its HTML content)."""
        if max_retries > 0:
            browser = self.tls.playwright.chromium.launch(headless=True)
            context = browser.new_context(accept_downloads=False, user_agent=self.user_agent)
            page = context.new_page()
            self.tls.current_page[threading.current_thread().name] = {"url": url, "js": ""}
            try:
                page.route("**/*.*", self._check_resource)
                sleep(randint(0, 6))
                page.goto(url, timeout=self.timeout * 1000)
                content = page.content()
                js_sha = hashlib.sha256(self.tls.current_page[threading.current_thread().name]["js"].encode('utf-8')).hexdigest()
                html_sha = hashlib.sha256(content.encode('utf-8')).hexdigest()
                print(js_sha)
                print(f"done get page from thread: {threading.current_thread().name}")
                page.close()
                context.close()
                browser.close()
                return url, content
            except Exception as e:
                print(f"Error: {e}")
                page.close()
                context.close()
                browser.close()
                if max_retries > 0:
                    print("Waiting 1 second before retrying...")
                    sleep(1)
                    print(f"Retrying: {url} >> {max_retries} more time(s)...")
                    return self._get_page_content(url, max_retries - 1)
                return url, ""
        return url, ""

    def crawl(self):
        """Start crawling all the pages of the website."""
        try:
            self.validate_website()
            self.tls = threading.local()
            self.thread_pool = ThreadPoolExecutor(
                max_workers=self.max_concurrent_requests, initializer=self._init_worker, initargs=(self.tls,)
            )
            self.start_crawl_time = timezone.now()
            self._crawl_at_current_depth({self.website})
            self.end_crawl_time = timezone.now()
            print(f"Crawling '{self.website}' ({len(self.visited_url)} pages) done in {self.end_crawl_time - self.start_crawl_time}.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.thread_pool.shutdown(wait=False)

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

class CrawlerModal:
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
            timeout: int = 15,
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
        # Temporary storage for JS content
        self.pages_js = {}
        # Crawl stats
        self.current_depth = 0
        self.start_crawl_time = None
        self.end_crawl_time = None
        self.visited_url = set()
        self.internal_links = []
        self.pages = set()

    @staticmethod
    def _remove_trailing_slash(url: str) -> str:
        """Remove trailing slash from URL (if any)."""
        if url.endswith('/'):
            return url[:-1]
        return url

    def _crawl_at_current_depth(self, pages: set[str]):
        """Crawl all the pages at the current depth."""
        pages_at_current_depth = list(pages)
        internal_urls_found = []
        limit = self.max_concurrent_requests
        print(f"Getting content of pages at depth {self.current_depth}...")

        while pages_at_current_depth:
            print(f"Pages left: {len(pages_at_current_depth)}")
            current_batch_urls = pages_at_current_depth[:limit]
            pages_content = []
            f = modal.Function.lookup("noname", "visit_page", environment_name="dev")
            for res in f.map(current_batch_urls):
                pages_content.append(res)
            for url, html in pages_content:
                internal_urls_found.extend(self._get_internal_links(html, url))
            self.visited_url |= set(current_batch_urls)
            del pages_at_current_depth[:limit]

        new_internal_urls = set(internal_urls_found) - self.visited_url
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
                href.startswith("mailto") or href.startswith("tel") or href.startswith("javascript")
            ):
                continue
            if not href.startswith('http'):
                leading_slash = '' if href.startswith('/') else '/'
                href = self.website + leading_slash + href
            if '#' in href:
                href = href.split('#')[0]
            if href.startswith('http://' + self.domain) or href.startswith('https://' + self.domain) and not href.endswith('.pdf'):
                internal_link = self._remove_trailing_slash(href)
                yield internal_link

    def _check_resource(self, route: Route) -> None:
        """Abort requests for non-HTML/JS resources. We don't want to download them."""
        if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
            route.abort()
        elif route.request.resource_type == "script":
            exclude_list = ["analytics.js", "gtm.js", "matomo.js"]
            if any(script for script in exclude_list if script in route.request.url):
                route.abort()
            else:
                res = route.fetch()
                self.tls.current_page[threading.current_thread().name]["js"] += res.text()
                route.continue_()
        else:
            route.continue_()

    def _get_page_content(self, url: str, max_retries: int = 3) -> tuple[str, str]:
        """Return a tuple containing: (URL of the page, its HTML content)."""
        if max_retries > 0:
            browser = self.tls.playwright.chromium.launch(headless=True)
            context = browser.new_context(accept_downloads=False, user_agent=self.user_agent)
            page = context.new_page()
            self.tls.current_page[threading.current_thread().name] = {"url": url, "js": ""}
            try:
                page.route("**/*.*", self._check_resource)
                sleep(randint(0, 6))
                page.goto(url, timeout=self.timeout * 1000)
                content = page.content()
                js_sha = hashlib.sha256(self.tls.current_page[threading.current_thread().name]["js"].encode('utf-8')).hexdigest()
                html_sha = hashlib.sha256(content.encode('utf-8')).hexdigest()
                print(js_sha)
                print(f"done get page from thread: {threading.current_thread().name}")
                page.close()
                context.close()
                browser.close()
                return url, content
            except Exception as e:
                print(f"Error: {e}")
                page.close()
                context.close()
                browser.close()
                if max_retries > 0:
                    print("Waiting 1 second before retrying...")
                    sleep(1)
                    print(f"Retrying: {url} >> {max_retries} more time(s)...")
                    return self._get_page_content(url, max_retries - 1)
                return url, ""
        return url, ""

    def crawl(self):
        """Start crawling all the pages of the website."""
        try:
            self.validate_website()
            self.start_crawl_time = timezone.now()
            self._crawl_at_current_depth({self.website})
            self.end_crawl_time = timezone.now()
            print(f"Crawling '{self.website}' ({len(self.visited_url)} pages) done in {self.end_crawl_time - self.start_crawl_time}.")
        except Exception as e:
            print(f"Error: {e}")

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
