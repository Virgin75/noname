from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, Permission, PermissionsMixin
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from users.managers import CustomUserManager


class Account(AbstractBaseUser, PermissionsMixin):
    """User model used in the app: stores basic information about the user (first name, last name...).

    Nice to know:
    - Each user must belong to a Company (and only one).
    - Two users can't have the same email address (identifier field).
    """

    class Meta:
        verbose_name_plural = "Users"

    email = models.EmailField(_("email address"), unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    company = models.ForeignKey("Company", on_delete=models.CASCADE, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    @property
    def initials(self) -> str | None:
        """Returns the initials of the user (capitalized)."""
        return f"{self.first_name[0]}{self.last_name[0]}".upper() if self.first_name and self.last_name else None

    def get_app_permissions(self) -> dict:  # noqa
        """Returns the list of cached grouped permissions for this user instance (1h cache)."""
        perms = cache.get(f"perms_{self.id}")
        if perms:
            return perms
        if not perms:
            group_perms = ["contacts", "pages", "products", "emails"] + settings.PLUGIN_APPS
            perms_choices = {
                group: [{f"{group}_{perm}": False} for perm in ("read_only_access", "full_access")]
                for group in group_perms
            }
            perms_choices["extra"] = [{"extra_can_export": False}, {"extra_company_admin": False}]
            permissions = [p.codename for p in self.user_permissions.all().only("codename")]
            for perm in permissions:
                for group in perms_choices:
                    for choice in perms_choices[group]:
                        if perm in choice:
                            choice[perm] = True
            cache.set(f"perms_{self.id}", perms_choices, 60 * 60)
            return perms_choices


class Company(models.Model):
    """A Company is an entity gathering users together.

    Every user has a single Company. A company can have multiple users.

    This table stores basic information about the company (name, address...).
    💡 Throughout the app, the Company is used to filter data the user has access to. Most
     of the others tables in db have a foreign key to Company.
    """

    name = models.CharField(max_length=80, unique=True)
    address = models.CharField(max_length=80, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name_plural = "Companies"

    @property
    def slug_name(self) -> str:
        """Returns the slugified name of the company (only characters that are accepted in URL or file names)."""
        return slugify(self.name)
