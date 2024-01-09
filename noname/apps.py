import logging

from django.apps import AppConfig
from django.db import transaction

logger = logging.getLogger(__name__)


class MainAppConfig(AppConfig):
    """Django configuration for `noname` app (main app)."""

    name = "noname"

    def ready(self):
        pass
