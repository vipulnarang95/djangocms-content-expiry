from django.contrib import admin

from cms.test_utils.testcases import CMSTestCase

import datetime
from djangocms_versioning.constants import PUBLISHED

from djangocms_content_expiry.test_utils.polls.factories import PollContentExpiryFactory


class ContentExpiryMonkeyPatchTesCase(CMSTestCase):
    def test_extended_admin_monkey_patch_list_display_expires(self):
        """
        Monkey patch should add expiry column and values to admin menu list display
        """
        from_date = datetime.datetime.now()

        delta_1 = datetime.timedelta(days=1)
        expire_at_1 = from_date + delta_1
        version = PollContentExpiryFactory(expires=expire_at_1, version__state=PUBLISHED)
        request = self.get_request("/")

        version_admin = admin.site._registry[type(version)]
        list_display = version_admin.get_list_display(request)

        # List display field should have been added by monkeypatch
        self.assertIn('expires', list_display)
