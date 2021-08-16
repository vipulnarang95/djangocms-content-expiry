from django.conf import settings

from cms.app_base import CMSAppConfig


class ContentExpiryAppConfig(CMSAppConfig):
    djangocms_content_expiry_enabled = getattr(
        settings, "DJANGOCMS_CONTENT_EXPIRY_ENABLED", True
    )
