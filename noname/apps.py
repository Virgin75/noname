import logging

from django.apps import AppConfig
from django.db import transaction

logger = logging.getLogger(__name__)


class MainAppConfig(AppConfig):
    """Django configuration for `noname` app (main app)."""

    name = "noname"

    def ready(self):
        """Run this code when the app is ready (successfully loaded)."""  # noqa
        from django.conf import settings
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        @transaction.atomic
        def add_custom_permissions():
            """Create default perms used throughout the app on 'post_migrate' signal."""
            ct = ContentType.objects.get(app_label="users", model="account")
            app_perms = ["contacts", "pages", "products", "emails"] + settings.PLUGIN_APPS
            for app in app_perms:
                Permission.objects.get_or_create(
                    name=f"Can access {app} page.", codename=f"{app}_full_access", content_type=ct
                )
                Permission.objects.get_or_create(
                    name=f"Can access {app} page.", codename=f"{app}_read_only_access", content_type=ct
                )

            # Special permissions (not app related)
            Permission.objects.get_or_create(
                name="Can use the export feature.", codename="extra_can_export", content_type=ct
            )
            Permission.objects.get_or_create(
                name="Can edit the Company settings and invite new members.",
                codename="extra_company_admin",
                content_type=ct,
            )

        add_custom_permissions()
