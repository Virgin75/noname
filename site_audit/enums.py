from django.db import models


class CrawlStatus(models.TextChoices):
    """List of all possible crawl status."""
    PENDING = "PENDING", "The crawl is pending."
    RUNNING = "RUNNING", "The crawl is running."
    SUCCESS = "SUCCESS", "The crawl has been successfully done."
    FAILED = "FAILED", "The crawl failed."


class AuditChoices(models.TextChoices):
    """List of all available audits ran daily on all pages of a website."""
    CRAWL_DEPTH = "CRAWL_DEPTH", "The current crawl depth of the page."
    STATUS_CODE = "STATUS_CODE", "The status code of the page."
    IS_INDEXABLE = "IS_INDEXABLE", "The page is indexable, not blocked by any robots.txt or meta tag rule."
    HAS_URL_ISSUES = "HAS_URL_ISSUES", "The crawled page has URL issues: non ascii char, params, space."
    HAS_META_TITLE = "HAS_META_TITLE", "The crawled page has a meta title."
    HAS_META_DESCRIPTION = "HAS_META_DESCRIPTION", "The crawled page has a meta description."
    HAS_ONLY_ONE_H1 = "HAS_ONLY_ONE_H1", "The crawled page has only one H1 tag."
    HAS_NO_REDIRECT_CHAIN = "HAS_NO_REDIRECT_CHAIN", "The crawled page has no redirect chain."
    HAS_VALID_HREFLANG = "HAS_VALID_HREFLANG", "The crawled page has valid hreflang tags."
    USES_HTTPS = "USES_HTTPS", "The page uses HTTPS."
    # Google Page Speed insights Performance metrics/audits
    PSI_PERFORMANCE_SCORE = "PSI_PERFORMANCE_SCORE", "The Google Page Speed Insights performance score."
    PSI_LARGEST_CONTENTFUL_PAINT = "PSI_LARGEST_CONTENTFUL_PAINT", "The Google Page Speed Insights LCP."
    PSI_TIME_TO_INTERACTIVE = "PSI_TIME_TO_INTERACTIVE", "The Google Page Speed Insights TTI."
    PSI_TOTAL_BLOCKING_TIME = "PSI_TOTAL_BLOCKING_TIME", "The Google Page Speed Insights TBT."
    PSI_CUMULATIVE_LAYOUT_SHIFT = "PSI_CUMULATIVE_LAYOUT_SHIFT", "The Google Page Speed Insights CLS."
    PSI_SPEED_INDEX = "PSI_SPEED_INDEX", "The Google Page Speed Insights Speed Index."
    PSI_FIRST_CONTENTFUL_PAINT = "PSI_FIRST_CONTENTFUL_PAINT", "The Google Page Speed Insights FCP."



