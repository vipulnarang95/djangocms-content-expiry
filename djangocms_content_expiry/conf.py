from django.conf import settings


DEFAULT_RANGEFILTER_DELTA = getattr(
    settings, "CMS_CONTENT_EXPIRY_DEFAULT_RANGEFILTER_DELTA", 30
)
