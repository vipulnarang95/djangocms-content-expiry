from unittest.mock import patch

from cms.test_utils.testcases import CMSTestCase

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from djangocms_content_expiry.test_utils.factories import (
    DefaultContentExpiryConfigurationFactory,
)
from djangocms_content_expiry.test_utils.polls.factories import PollContentExpiryFactory
from djangocms_content_expiry.utils import get_default_duration_for_version


class ContentExpiryDefaultConfigurationHelperTestCase(CMSTestCase):

    @freeze_time("2200-01-14")
    @patch('djangocms_content_expiry.utils.DEFAULT_CONTENT_EXPIRY_DURATION', 1)
    def test_default_duration_for_content_type(self):
        """
        Default durations for Content Type can be set via a setting or by a content
        author using DefaultContentExpiryConfiguration.
        """
        poll_content_expiry = PollContentExpiryFactory()

        # Value before default expiry date is set, expected to use
        # the value of: DEFAULT_CONTENT_EXPIRY_DURATION
        no_default_duration = 1
        no_default_actual_result = get_default_duration_for_version(poll_content_expiry.version)
        no_default_expected_result = relativedelta(months=no_default_duration)

        self.assertEqual(no_default_actual_result, no_default_expected_result)

        # After creating an entry the expected value should be the value set here...
        DefaultContentExpiryConfigurationFactory(
            content_type=poll_content_expiry.version.content_type,
            duration=3
        )

        has_default_duration = 3
        has_default_actual_result = get_default_duration_for_version(poll_content_expiry.version)
        has_default_expected_result = relativedelta(months=has_default_duration)

        # Ensure a fair test by enforcing that the values set have to be different
        self.assertNotEqual(no_default_duration, has_default_duration)
        self.assertEqual(has_default_actual_result, has_default_expected_result)
