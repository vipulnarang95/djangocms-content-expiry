from cms.test_utils.testcases import CMSTestCase

from djangocms_content_expiry.helpers import get_authors
from djangocms_content_expiry.test_utils.polls.factories import PollContentExpiryFactory


class ContentExpiryHelpersTestCase(CMSTestCase):
    def test_get_authors_query_burden(self):
        """
        Ensure that the get_authors helper does not execute multiple queries
        """
        PollContentExpiryFactory.create_batch(20)
        with self.assertNumQueries(1):
            users = get_authors()
            self.assertEqual(users.count(), 20)
