from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from djangocms_versioning.models import Version

from .constants import CONTENT_EXPIRY_EXPIRE_FIELD_LABEL


class ContentExpiry(models.Model):
    created = models.DateTimeField(auto_now_add=True)
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
