from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from djangocms_versioning.models import Version

from .conf import DEFAULT_CONTENT_EXPIRY_DURATION
from .constants import CONTENT_EXPIRY_EXPIRE_FIELD_LABEL


def _limit_content_type_choices():
    """
    Get a limited list of the content types that the
    DefaultContentExpiryConfiguration model can use
    """
    from .utils import get_versionable_content_types

    content_type_list = get_versionable_content_types()
    inclusion = [content_type.pk for content_type in content_type_list]
    return {"id__in": inclusion}


class ContentExpiry(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    compliance_number = models.CharField(max_length=30, blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_('expired by')
    )
    version = models.OneToOneField(
        Version,
        on_delete=models.CASCADE,
        verbose_name=_('version')
    )
    expires = models.DateTimeField(CONTENT_EXPIRY_EXPIRE_FIELD_LABEL)

    class Meta:
        verbose_name = _("Content Expiry")
        verbose_name_plural = _("Content Expiry")


class DefaultContentExpiryConfiguration(models.Model):
    content_type = models.OneToOneField(
        ContentType,
        primary_key=True,
        limit_choices_to=_limit_content_type_choices,
        on_delete=models.CASCADE,
        verbose_name=_('content type')
    )
    duration = models.IntegerField(help_text=_("Duration in months"), default=DEFAULT_CONTENT_EXPIRY_DURATION)

    class Meta:
        verbose_name = _("Content Type Configuration")
        verbose_name_plural = _("Content Type Configuration")

    def __str__(self):
        return str(self.content_type)
