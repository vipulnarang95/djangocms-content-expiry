from django.conf import settings

from cms.app_base import CMSAppConfig
from cms.utils.i18n import get_language_tuple

from .models import ContentExpiryContent


class ContentExpiryAppConfig(CMSAppConfig):
    djangocms_versioning_enabled = getattr(
        settings, "DJANGOCMS_NAVIGATION_VERSIONING_ENABLED", True
    )
    djangocms_moderation_enabled = getattr(
        settings, "DJANGOCMS_NAVIGATION_MODERATION_ENABLED", True
    )

    if djangocms_versioning_enabled:
        from djangocms_versioning.datastructures import VersionableItem, default_copy

        versioning = [
            VersionableItem(
                content_model=ContentExpiryContent,
                grouper_field_name="page_type",
                version_list_filter_lookups={"language": get_language_tuple},
                copy_function=default_copy
            )
        ]
