from cms.api import create_page
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import signal_tester

from djangocms_versioning import constants, signals
from djangocms_versioning.models import Version

from djangocms_content_expiry.models import ContentExpiry
from djangocms_content_expiry.test_utils.polls.factories import (
    PollFactory,
    PollVersionFactory,
)


class ContentExpirySignalTestCase(CMSTestCase):
    def test_content_expiry_creation_signal(self):
        """
        Content expiry should exist in new versions, always.
        """
        language = "en"
        user = self.get_superuser()
        page = create_page(
            title="home",
            template="page.html",
            language=language,
            created_by=user
        )

        version = Version.objects.filter_by_grouper(page)
        expiry_record = ContentExpiry.objects.filter(version=version[0])
        self.assertEqual(len(expiry_record), 1)
        self.assertTrue(hasattr(expiry_record[0], "expires"))

    def test_submitted_for_review_signal(self):
        """
        Creating a new page should emit a signal to create a content expiry entry
        and should only execute on creating a draft
        """
        with signal_tester(signals.post_version_operation) as env:
            language = "en"
            user = self.get_superuser()
            create_page(
                title="home",
                template="page.html",
                language=language,
                created_by=user
            )

            self.assertEqual(env.call_count, 1)
            signal = env.calls[0][1]
            self.assertEqual(signal["operation"], constants.OPERATION_DRAFT)

    def test_content_expiry_creation_for_polls(self):
        """
        Creating a new poll should emit a signal to create a content expiry entry
        and should only execute on creating a draft
        """
        with signal_tester(signals.post_version_operation) as env:
            poll = PollFactory()
            version = PollVersionFactory(
                state=constants.DRAFT, content__poll=poll
            )

            self.assertEqual(env.call_count, 1)
            signal = env.calls[0][1]
            self.assertEqual(
                signal["sender"], version.content_type.model_class()
            )
            self.assertEqual(signal["operation"], constants.OPERATION_DRAFT)
            self.assertEqual(signal["obj"], version)
