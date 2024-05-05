from datetime import timedelta

from django.db import models

from site_audit.enums import AuditChoices, CrawlStatus


class DailyCrawl(models.Model):
    """Represents a daily crawl of a website."""
    company = models.ForeignKey("users.Company", on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=CrawlStatus.choices, default=CrawlStatus.RUNNING)

    @property
    def duration(self) -> timedelta:
        """Return the duration of the crawl."""
        return self.finished_at - self.started_at


class Page(models.Model):
    """Represents a webpage discovered by a Crawler."""

    url = models.URLField(max_length=1000, unique=True, db_index=True)
    first_crawl_at = models.DateTimeField(auto_now_add=True)
    last_crawl_at = models.DateTimeField(auto_now=True)
    content_sha256 = models.CharField(max_length=64)
    company = models.ForeignKey("users.Company", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("company", "url")
        indexes = [
            models.Index(fields=["company", "url"]),
        ]

    def __str__(self):
        return self.url

    def __eq__(self, other):
        """Consider two Pages are equal if their URLs are equal."""
        return self.url == other.url

    def __hash__(self):
        """Return the hash of the URL."""
        return hash(self.url)


class DailyPageMetric(models.Model):
    """
    Represents a daily metric for a webpage.

    Everyday, the crawler gather a lot of different metrics on a page. This table is used to store these metrics.
    """
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="metrics")
    company = models.ForeignKey("users.Company", on_delete=models.CASCADE)
    metric_value = models.FloatField()
    metric_name = models.CharField(max_length=50, db_index=True, choices=AuditChoices.choices, blank=False, null=False)
    metric_date = models.DateField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = ("page", "metric_name", "metric_date")
        indexes = [
            models.Index(fields=["page", "company", "metric_date", "metric_name"]),
        ]


class DailySiteMetric(models.Model):
    """
    Represents a daily metric record for the whole website.

    It represents an aggregation of all daily metrics of all the pages.
    """
    company = models.ForeignKey("users.Company", on_delete=models.CASCADE)
    metric_value = models.FloatField()
    metric_name = models.CharField(max_length=50, db_index=True)
    metric_date = models.DateField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = ("company", "metric_name", "metric_date")
        indexes = [
            models.Index(fields=["company", "metric_date"]),
        ]