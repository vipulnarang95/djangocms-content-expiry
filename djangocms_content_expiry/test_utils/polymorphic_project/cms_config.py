from cms.app_base import CMSAppConfig

from djangocms_versioning.admin import VersioningAdminMixin
from djangocms_versioning.datastructures import (
    PolymorphicVersionableItem,
    VersionableItemAlias,
    default_copy,
)

from .models import ArtProjectContent, ProjectContent, ResearchProjectContent


def versioning_project_models_config():
    file_config = PolymorphicVersionableItem(
        content_model=ProjectContent,
        grouper_field_name='grouper',
        copy_function=default_copy,
        content_admin_mixin=VersioningAdminMixin,
    )
    yield file_config

    for model in [ArtProjectContent, ResearchProjectContent]:
        model._meta._get_fields_cache = {}
        yield VersionableItemAlias(
            content_model=model,
            to=file_config,
        )


class PolymorphicCMSConfig(CMSAppConfig):
    djangocms_versioning_enabled = True
    versioning = list(versioning_project_models_config())
