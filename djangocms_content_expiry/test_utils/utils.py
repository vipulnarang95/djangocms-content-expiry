from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from djangocms_versioning.datastructures import VersionableItemAlias


def _get_content_types_set():
    """
    Get a unique list of versionables that are not polymorphic
    """
    versioning_config = apps.get_app_config("djangocms_versioning")
    content_types = []

    for versionable in versioning_config.cms_extension.versionables:
        if not isinstance(versionable, VersionableItemAlias):
            content_type = ContentType.objects.get_for_model(versionable.content_model)
            content_types.append(content_type.pk)

    # The list is equal to the content type versionables, get a unique list
    return set(content_types)
