import datetime

from django.contrib import admin
from django.test import RequestFactory

from cms.test_utils.testcases import CMSTestCase

from djangocms_versioning.constants import PUBLISHED

from djangocms_content_expiry.constants import CONTENT_EXPIRY_EXPIRE_FIELD_LABEL
from djangocms_content_expiry.test_utils.polls.factories import PollContentExpiryFactory


class ContentExpiryMonkeyPatchTesCase(CMSTestCase):

    def test_extended_admin_monkey_patch_list_display_expires(self):
        """
        Monkey patch should add expiry column and values to admin menu list display
        """
        from_date = datetime.datetime.now()

        delta_1 = datetime.timedelta(days=1)
        expire_at_1 = from_date + delta_1
        content_expiry = PollContentExpiryFactory(expires=expire_at_1, version__state=PUBLISHED)
        version_admin = admin.site._registry[content_expiry.version.versionable.version_model_proxy]

        request = RequestFactory().get("/")
        list_display = version_admin.get_list_display(request)

        # List display field should have been added by monkeypatch
        self.assertIn('expire', list_display)
        self.assertEqual(CONTENT_EXPIRY_EXPIRE_FIELD_LABEL, version_admin.expire.short_description)
