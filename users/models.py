from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from users.managers import CustomUserManager


class Account(AbstractBaseUser, PermissionsMixin):
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

    def __str__(self):
        return self.email


class Company(models.Model):
    name = models.CharField(max_length=80, unique=True)
    address = models.CharField(max_length=80, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name_plural = "Companies"

    @property
    def slug_name(self):
        return slugify(self.name)

    def __str__(self):
        return self.name
