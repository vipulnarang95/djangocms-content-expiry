from datetime import datetime
from unittest.mock import patch

from cms.test_utils.testcases import CMSTestCase

from freezegun import freeze_time

from djangocms_content_expiry.helpers import (
    get_authors,
    get_rangefilter_expires_default,
)
from djangocms_content_expiry.test_utils.polls.factories import PollContentExpiryFactory


class ContentExpiryAuthorHelperTestCase(CMSTestCase):
    def test_get_authors_query_burden(self):
        """
        Ensure that the get_authors helper does not execute multiple queries
        """
        PollContentExpiryFactory.create_batch(20)
        with self.assertNumQueries(1):
            users = get_authors()
            self.assertEqual(users.count(), 20)


class ContentExpiryDefaultRangeHelperTestCase(CMSTestCase):

    @patch('djangocms_content_expiry.helpers.DEFAULT_RANGEFILTER_DELTA', 5)
    def test_default_range_is_returned_from_setting_value(self):
        """
        By default the range returned should be changed by the setting:
        CMS_CONTENT_EXPIRY_DEFAULT_RANGEFILTER_DELTA mapped in conf.py as
        DEFAULT_RANGEFILTER_DELTA
        """
        with freeze_time("2100-10-10 00:00:00", tz_offset=0):
            start, end = get_rangefilter_expires_default()

        self.assertEqual(start, datetime(2100, 10, 5, 0, 0))
        self.assertEqual(end, datetime(2100, 10, 10, 0, 0))
