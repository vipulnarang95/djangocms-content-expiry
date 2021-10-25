from datetime import datetime, timedelta

from djangocms_content_expiry.conf import DEFAULT_RANGEFILTER_DELTA


def get_rangefilter_expires_default():
    """
    Sets a default date range to help filter
    Content Expiry records
    """
    start_date = datetime.now()
    end_date = datetime.now() + timedelta(DEFAULT_RANGEFILTER_DELTA)
    return start_date, end_date
