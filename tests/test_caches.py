import datetime
from unittest.mock import patch

from cms.test_utils.testcases import CMSTestCase

from freezegun import freeze_time

from djangocms_content_expiry.cache import (
    get_changelist_page_content_exclusion_cache,
    set_changelist_page_content_exclusion_cache,
)


class ContentExpiryPageContentCacheMechanismTestCase(CMSTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.initial_datetime = datetime.datetime.now()

    @patch('djangocms_content_expiry.cache.DEFAULT_CONTENT_EXPIRY_CHANGELIST_PAGECONTENT_EXCLUSION_CACHE_EXPIRY', 123)
    def test_content_expiry_cache_expiration(self):
        """
        Creating a new PageContent object should empty the existing cache entry
        """
        site_id = 1
        value = [1]

        with freeze_time(self.initial_datetime) as frozen_datetime:

            set_changelist_page_content_exclusion_cache(value, site_id)
            cached_value = get_changelist_page_content_exclusion_cache(site_id)

            self.assertEqual(cached_value, value)

            # Simulate 122 seconds passing, i.e. cache is still valid
            frozen_datetime.tick(delta=datetime.timedelta(seconds=122))

            cached_value = get_changelist_page_content_exclusion_cache(site_id)

            # The cache should be used and valid
            self.assertEqual(cached_value, value)

            # Simulate 123 seconds passing, i.e. cache is now invalid
            frozen_datetime.tick(delta=datetime.timedelta(seconds=123))

            cached_value = get_changelist_page_content_exclusion_cache(site_id)

            # The cache should now be have expired
            self.assertNotEqual(cached_value, value)
            self.assertEqual(cached_value, None)

    @patch('djangocms_content_expiry.cache.DEFAULT_CONTENT_EXPIRY_CHANGELIST_PAGECONTENT_EXCLUSION_CACHE_EXPIRY', 123)
    def test_content_expiry_cache_expiration_multiple_sites(self):
        """
        Creating a new  object should empty the existing cache entry
        """
        site_1_id = 1
        site_2_id = 2
        site_1_value = [1, 2, 3, 4]
        site_2_value = [5, 6, 7, 8]

        with freeze_time(self.initial_datetime) as frozen_datetime:
            # Populate site 1 cache
            set_changelist_page_content_exclusion_cache(site_1_value, site_1_id)
            site_1_cached_value = get_changelist_page_content_exclusion_cache(site_1_id)
            # Populate site 2 cache
            set_changelist_page_content_exclusion_cache(site_2_value, site_2_id)
            site_2_cached_value = get_changelist_page_content_exclusion_cache(site_2_id)

            self.assertEqual(site_1_cached_value, site_1_value)
            self.assertEqual(site_2_cached_value, site_2_value)
            self.assertNotEqual(site_1_cached_value, site_2_cached_value)

            # Simulate 122 seconds passing, i.e. cache is still valid
            frozen_datetime.tick(delta=datetime.timedelta(seconds=122))

            site_1_cached_value = get_changelist_page_content_exclusion_cache(site_1_id)
            site_2_cached_value = get_changelist_page_content_exclusion_cache(site_2_id)

            # The cache should be used and valid
            self.assertEqual(site_1_cached_value, site_1_value)
            self.assertEqual(site_2_cached_value, site_2_value)
            self.assertNotEqual(site_1_cached_value, site_2_cached_value)

            # Simulate 123 seconds passing, i.e. cache is now invalid
            frozen_datetime.tick(delta=datetime.timedelta(seconds=123))

            site_1_cached_value = get_changelist_page_content_exclusion_cache(site_1_id)
            site_2_cached_value = get_changelist_page_content_exclusion_cache(site_2_id)

            # The cache should now be have expired
            self.assertNotEqual(site_1_cached_value, site_1_value)
            self.assertNotEqual(site_2_cached_value, site_2_value)
            self.assertEqual(site_1_cached_value, None)
            self.assertEqual(site_2_cached_value, None)
