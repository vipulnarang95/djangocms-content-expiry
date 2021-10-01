from django.conf import settings


# Default range filter control in days
DEFAULT_RANGEFILTER_DELTA = getattr(
    settings, "CMS_CONTENT_EXPIRY_DEFAULT_RANGEFILTER_DELTA", 30
)

# Default Content Expiry duration in months
DEFAULT_CONTENT_EXPIRY_DURATION = getattr(
    settings, "CMS_CONTENT_EXPIRY_DEFAULT_CONTENT_EXPIRY_DURATION", 12
)
