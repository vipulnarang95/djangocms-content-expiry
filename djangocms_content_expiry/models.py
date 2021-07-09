from django.db import models
from django.utils.translation import ugettext_lazy as _


class ContentExpiry(models.Model):
    label = models.CharField(verbose_name=_('label'), max_length=100)

    class Meta:
        verbose_name = _("Content Expiry")
