from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _

import datetime


class ContentExpiry(models.Model):
    pass


class ContentExpiryContent(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    from_expiry_date = models.DateField(_("From Expiry Date"), default=datetime.date.today)
    to_expiry_date = models.DateField(_("To Expiry Date"), default=datetime.date.today)

    class Meta:
        verbose_name = _("Content Expiry")
