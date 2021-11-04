from django.core.cache import cache

from djangocms_content_expiry.conf import (
    DEFAULT_CONTENT_EXPIRY_CHANGELIST_PAGECONTENT_EXCLUSION_CACHE_EXPIRY,
)
from djangocms_content_expiry.constants import (
    CONTENT_EXPIRY_CHANGELIST_PAGECONTENT_EXCLUSION_CACHE_KEY,
)


def _get_cache_key(site_id):
    return f"{CONTENT_EXPIRY_CHANGELIST_PAGECONTENT_EXCLUSION_CACHE_KEY}_{site_id}"


def set_changelist_page_content_exclusion_cache(value, site_id):
    """
    Populate the cache that is set to never expire!

    :param value: A value to set the cache object with
    :param site_id: The site id to get the correct cache entry
    """
    cache_key = _get_cache_key(site_id)
    cache.set(
        cache_key,
        value,
        timeout=DEFAULT_CONTENT_EXPIRY_CHANGELIST_PAGECONTENT_EXCLUSION_CACHE_EXPIRY
    )


def get_changelist_page_content_exclusion_cache(site_id):
    """
    Get the cached value if it exists.

    :returns: the cache if it is set, or None if it the key doesn't exist.
    :param site_id: The site id to get the correct cache entry
    """
    cache_key = _get_cache_key(site_id)
    return cache.get(cache_key)
