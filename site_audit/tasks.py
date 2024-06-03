import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from random import randint
from time import sleep

from playwright.sync_api import sync_playwright, Route
from typing import Generator

from bs4 import BeautifulSoup

import django
import modal
from modal import Image


site_audit = modal.App("site_audit")
django_app_image = (
    Image.debian_slim(python_version="3.11")
    .pip_install_from_requirements("requirements.txt")
    .workdir("/app")
    .env({"DJANGO_SETTINGS_MODULE": "noname.settings"})
    .apt_install("curl", "chromium")
    .run_commands("curl -sL https://deb.nodesource.com/setup_20.x -o /tmp/nodesource_setup.sh", "bash /tmp/nodesource_setup.sh", "apt-get install nodejs -y", "playwright install", "playwright install-deps", "npm install -g lighthouse")
    .copy_local_dir("bin", "/app/bin")
    .copy_local_dir("commons", "/app/commons")
    .copy_local_dir("contacts", "/app/contacts")
    .copy_local_dir("users", "/app/users")
    .copy_local_dir("theme", "/app/theme")
    .copy_local_dir("noname", "/app/noname")
    .copy_local_dir("site_audit", "/app/site_audit")
    .copy_local_file("manage.py", "/app/manage.py")
)


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
            company = None,
            user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            exclude_patterns: list[str] = None,
            exclude_pages: list[str] = None,
            exclude_url_params: bool = True,
            timeout: int = 15,
            max_concurrent_requests: int = 5
    ):
        self.website = website
        self.company = company
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
        self.audits = []

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

    def _run_custom_audits(self, url: str, page_title: str, page_content: str) -> None:
        """Run custom audits on the page."""
        from site_audit.models import DailyPageAudit
        from commons.utils import call_func_from_str
        from site_audit.enums import AuditChoices

        for audit in AuditChoices.get_custom_audits():
            res = call_func_from_str(
                audit.path, url=url, page_title=page_title, page_content=page_content, depth=self.current_depth
            )
            audit_obj = DailyPageAudit(
                page_id=url, company=self.company, audit_id=audit.value, date=datetime.now().date(), audit_score=res
            )
            self.audits.append(audit_obj)

    def _check_resource(self, route: Route) -> None:
        """Abort requests for non-HTML/JS resources. We don't want to download them."""
        if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
            route.abort()
        elif route.request.resource_type == "script":
            exclude_list = ["analytics.js", "gtm.js", "matomo.js"]
            if any(script for script in exclude_list if script in route.request.url):
                route.abort()
            else:
                #TODO: check doc (might need fulfill)
                res = route.fetch()
                self.tls.current_page[threading.current_thread().name]["js"] += res.text()
                route.continue_()
        else:
            route.continue_()

    def _get_page_content(self, url: str, max_retries: int = 3) -> tuple[str, str]:
        """Return a tuple containing: (URL of the page, its HTML content)."""
        from site_audit.models import Page

        if max_retries > 0:
            browser = self.tls.playwright.chromium.launch(headless=True)
            context = browser.new_context(accept_downloads=False, user_agent=self.user_agent)
            page = context.new_page()
            self.tls.current_page[threading.current_thread().name] = {"url": url, "js": ""}
            try:
                page.route("**/*.*", self._check_resource)
                sleep(randint(0, 6))
                page.goto(url, timeout=self.timeout * 1000)
                content = str(page.content())
                title = str(page.title())
                sha = hashlib.sha256(self.tls.current_page[threading.current_thread().name]["js"].encode('utf-8') + content.encode('utf-8')).hexdigest()
                print(f"done get page from thread: {threading.current_thread().name}")
                #self._run_custom_audits(url, title, content)
                page.close()
                context.close()
                browser.close()
                self.pages.add(
                    Page(
                        url=url, content_sha256=sha, last_crawl_at=datetime.now(), company=self.company
                    )
                )
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
            self.start_crawl_time = datetime.now()
            self._crawl_at_current_depth({self.website})
            self.end_crawl_time = datetime.now()
            print(f"Crawling '{self.website}' ({len(self.visited_url)} pages) done in {self.end_crawl_time - self.start_crawl_time}.")
        finally:
            self.thread_pool.shutdown(wait=False)

    def validate_website(self) -> None:
        """Make sure 'self.website' is a valid URL and is the root page of website."""
        from django.core.validators import URLValidator
        from urllib.parse import urlparse

        if not self.website:
            raise ValueError("No website provided in Crawler init().")
        URLValidator()(self.website)  # raises ValidationError if not valid URL
        parsed_url = urlparse(self.website)
        # Keep only scheme and hostname (root)
        self.website = f"{parsed_url.scheme}://{parsed_url.hostname}"
        self.domain = parsed_url.hostname
        self.visited_url.add(self.website)


@site_audit.function(
    image=django_app_image,
    secrets=[modal.Secret.from_name("database")],
    timeout=3600*3
)
def run_psi_audit(urls: list[str] = None, company_id: int = None):
    """Run the Google Page Speed Insights audits via Lighthouse on a list of urls."""
    django.setup()
    import subprocess
    import json
    from commons.utils import OpenAndCloseDbConnection
    from commons.utils import get_nested_value
    from site_audit.enums import AuditChoices, CrawlStatus
    from site_audit.models import DailyPageAudit, DailyPsiAudit

    with OpenAndCloseDbConnection():
        DailyPsiAudit.objects.create(company_id=company_id, pages_audited=len(urls))

    audits = []
    for url in urls:
        ps = subprocess.Popen([
            "lighthouse",
            str(url),
            "--quiet",
            "--output=json",
            "--disable-full-page-screenshot",
            '--chrome-flags="--no-sandbox --headless"'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = ps.communicate()
        if stderr:
            print(stderr)
        else:
            # Create new 'DailyPageAudit' objects
            results = json.loads(stdout)
            for audit in AuditChoices.get_psi_audits():
                audit_result = get_nested_value(results, audit.path)
                audits.append(
                    DailyPageAudit(
                        audit_id=audit.value,
                        audit_score=audit_result,
                        page_id=url,
                        date=datetime.now().date(),
                        company_id=company_id
                    )
                )
    with OpenAndCloseDbConnection():
        daily_psi_stats = DailyPsiAudit.objects.get()
        try:
            DailyPageAudit.objects.bulk_create(audits, 1024)
            daily_psi_stats.status = CrawlStatus.SUCCESS
        except:
            daily_psi_stats.status = CrawlStatus.FAILED
        finally:
            daily_psi_stats.finished_at = datetime.now()
            daily_psi_stats.save()


@site_audit.function(image=django_app_image, timeout=3600*3, secrets=[modal.Secret.from_name("database")])
def crawl_website(company_id: int = None, crawl_id: int = None):
    """Start the crawl async task for a specific website."""
    django.setup()
    from commons.utils import OpenAndCloseDbConnection
    from site_audit.enums import CrawlStatus
    from site_audit.models import DailyCrawl, Page
    from users.models import Company

    try:
        company = None
        with OpenAndCloseDbConnection():
            company = Company.objects.get(id=company_id)
        crawler = Crawler(website=company.website, company=company)
        crawler.crawl()
        status = CrawlStatus.SUCCESS

        # Retrieve pages with updated content since last crawl
        updated_pages = []
        new_pages = []
        with OpenAndCloseDbConnection():
            existing_pages = Page.objects.filter(company_id=company_id).only("content_sha256").in_bulk(field_name="url")
            for page in crawler.pages:
                if page.url in existing_pages and existing_pages[page.url].content_sha256 != page.content_sha256:
                    updated_pages.append(page.url)
                elif page.url not in existing_pages:
                    new_pages.append(page.url)

            # Create new pages in the database and update existing ones
            Page.objects.bulk_create(
                crawler.pages,
                512,
                update_conflicts=True,
                update_fields=["last_crawl_at", "content_sha256"],
                unique_fields=["company", "url"]
            )

            # Save custom audits already run
            from site_audit.models import DailyPageAudit
            DailyPageAudit.objects.bulk_create(crawler.audits, 1024)

            # Run PSI audits on updated pages or new pages
            run_psi_audit.spawn(urls=set(updated_pages + new_pages), company_id=company_id)

    except Exception as e:
        status = CrawlStatus.FAILED
    finally:
        with OpenAndCloseDbConnection():
            crawl_log = DailyCrawl.objects.get(id=crawl_id)
            crawl_log.finished_at = datetime.now()
            crawl_log.status = status
            crawl_log.pages_crawled = len(crawler.visited_url)
            crawl_log.save()


@site_audit.function(
    image=django_app_image,
    schedule=modal.Cron("0 8 * * 1"),
    secrets=[modal.Secret.from_name("database")]
)
def daily_crawl():
    """Scheduled daily to start the crawling process on every website."""
    django.setup()
    from commons.utils import OpenAndCloseDbConnection
    from users.models import Company
    from site_audit.models import DailyCrawl

    with OpenAndCloseDbConnection():
        for company in Company.objects.only("id", "website"):
            crawl_log = DailyCrawl.objects.create(company=company)
            crawl_website.spawn(company_id=company.id, crawl_id=crawl_log.id)
