from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def get_app_version() -> str:
    return settings.APP_VERSION or "err"
