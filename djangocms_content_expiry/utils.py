from dateutil.relativedelta import relativedelta

from .conf import DEFAULT_CONTENT_EXPIRY_DURATION
from .models import DefaultContentExpiryConfiguration


def get_default_duration_for_version(version):
    """
    Returns a default expiration value dependant on whether an entry exists for
    a content type in DefaultContentExpiryConfiguration.
    """
    default_configuration = DefaultContentExpiryConfiguration.objects.filter(
        content_type=version.content_type
    )
    if default_configuration:
        return relativedelta(months=default_configuration[0].duration)
    return relativedelta(months=DEFAULT_CONTENT_EXPIRY_DURATION)


def get_future_expire_date(version, date):
    """
    Returns a date that will expire after a default period that can differ per content type
    """
    return date + get_default_duration_for_version(version)
