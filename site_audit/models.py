from datetime import timedelta, datetime

from django.db import models
from django.db.models import Sum, F

from site_audit.enums import AuditChoices, CrawlStatus
from users.models import Company


class DailyCrawl(models.Model):
    """Represents a daily crawl of a website + audits."""
    company = models.ForeignKey("users.Company", on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=CrawlStatus.choices, default=CrawlStatus.RUNNING)
    pages_crawled = models.IntegerField(default=0)

    @property
    def duration(self) -> timedelta:
        """Return the duration of the crawl."""
        return self.finished_at - self.started_at


class DailyPsiAudit(models.Model):
    """Represents a run of PSI audits (lighthouse) on all pages of a website."""
    company = models.ForeignKey("users.Company", on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=CrawlStatus.choices, default=CrawlStatus.RUNNING)
    pages_audited = models.IntegerField(default=0)

    @property
    def duration(self) -> timedelta:
        """Return the duration of the crawl."""
        return self.finished_at - self.started_at


class Page(models.Model):
    """Represents a webpage discovered by a Crawler."""

    url = models.URLField(max_length=1000, unique=True, db_index=True, primary_key=True)
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


class Audit(models.Model):
    """
    Represents a test executed on each webpage.
    """
    name = models.CharField(
        max_length=50, db_index=True, choices=AuditChoices.choices, blank=False, null=False, primary_key=True
    )
    category = models.CharField(max_length=50, db_index=True, blank=False, null=False)
    description = models.TextField()
    category_weight = models.FloatField(default=1.0)
    global_weight = models.FloatField(default=1.0)


class DailyPageAudit(models.Model):
    """
    Represents a daily audit value for a webpage.

    Everyday, the crawler gather a lot of different metrics on a page. This table is used to store these metrics.
    The score is always a float from 0.00 to 1.00.
    """
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="audits")
    company = models.ForeignKey("users.Company", on_delete=models.CASCADE)
    date = models.DateField(db_index=True)
    audit_score = models.FloatField(null=True)
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("page", "audit", "date")
        indexes = [
            models.Index(fields=["page", "company", "date", "audit", "audit_score"]),
        ]

    @classmethod
    def get_daily_category_avg(cls, for_company: Company = None, category: str = None):
        """Get the current daily score average for a given website (company), on a chosen audit category."""
        if for_company is None:
            raise ValueError("'for_company' kwargs is required.")

        today = datetime.now().strftime("%m-%d-%Y")
        return cls.objects.filter(
            company=for_company, date=today, audit__category=category
        ).aggregate(
            avg=Sum(F('audit__category_weight') * F('audit_score')) / Sum('audit__category_weight')
        )["avg"]


class DailySiteMetric(models.Model):
    """
    Represents a daily metric record for the whole website (average).

    It represents an aggregation of all daily metrics of all the pages.
    """
    company = models.ForeignKey("users.Company", on_delete=models.CASCADE)
    date = models.DateField(db_index=True)
    audit_avg_score = models.FloatField(null=True)
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("company", "audit", "date")
        indexes = [
            models.Index(fields=["company", "date", "audit", "audit_avg_score"]),
        ]