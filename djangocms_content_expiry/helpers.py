from datetime import datetime, timedelta

from django.contrib.auth import get_user_model

from djangocms_content_expiry.conf import DEFAULT_RANGEFILTER_DELTA


def get_authors():
    """
    Helper to return all authors created by content expiry
    """
    User = get_user_model()
    return User.objects.filter(contentexpiry__created_by__isnull=False).distinct()


def get_rangefilter_expires_default():
    """
    Sets a default date range to help filter
    Content Expiry records
    """
    start_date = datetime.now() - timedelta(DEFAULT_RANGEFILTER_DELTA)
    end_date = datetime.now()
    return start_date, end_date
