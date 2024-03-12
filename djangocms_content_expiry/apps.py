from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from djangocms_versioning import signals


class DjangocmsContentExpiryConfig(AppConfig):
    name = "djangocms_content_expiry"
    verbose_name = _("django CMS Content Expiry")

    def ready(self):
        from .handlers import create_content_expiry
        from .monkeypatch import admin as monkeypatch_admin  # noqa: F401

        signals.post_version_operation.connect(create_content_expiry)
