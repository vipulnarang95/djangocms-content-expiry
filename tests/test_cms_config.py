from django.apps import apps
from django.contrib import admin
from django.test import RequestFactory

from cms.test_utils.testcases import CMSTestCase

from djangocms_moderation.cms_config import ModerationExtension
from djangocms_moderation.models import ModerationRequestTreeNode

from djangocms_content_expiry.cms_config import ContentExpiryAppConfig
from djangocms_content_expiry.constants import CONTENT_EXPIRY_EXPIRE_FIELD_LABEL


class ModerationConfigDependancyTestCase(CMSTestCase):
    def test_moderation_config_admin_controls_exist(self):
        """
        Moderation controls are required for the content expiry records to be viewed,
        ensure that they exist, a failure here means that the implementation in moderation
        may have been changed
        """
        moderation_extension = ModerationExtension()

        self.assertTrue(hasattr(moderation_extension, "moderation_request_changelist_actions"))
        self.assertTrue(hasattr(moderation_extension, "moderation_request_changelist_fields"))
        self.assertTrue(
            hasattr(moderation_extension, "handle_moderation_request_changelist_actions")
            and callable(moderation_extension.handle_moderation_request_changelist_actions)
        )
        self.assertTrue(
            hasattr(moderation_extension, "handle_moderation_request_changelist_fields")
            and callable(moderation_extension.handle_moderation_request_changelist_fields)
        )

    def test_moderation_config_admin_controls_are_compiled_by_moderation(self):
        moderation = apps.get_app_config("djangocms_moderation")
        content_expiry_actions = ContentExpiryAppConfig.moderation_request_changelist_actions
        content_expiry_fields = ContentExpiryAppConfig.moderation_request_changelist_fields

        self.assertListEqual(
            moderation.cms_extension.moderation_request_changelist_actions,
            content_expiry_actions,
        )
        self.assertListEqual(
            moderation.cms_extension.moderation_request_changelist_fields,
            content_expiry_fields,
        )

    def test_moderation_request_contains_added_admin_fields(self):
        """
        Ensure that the admin field is added as expected
        """
        moderation_admin = admin.site._registry[ModerationRequestTreeNode]

        request = RequestFactory().get("/")
        list_display = moderation_admin.get_list_display(request)

        self.assertIn('get_expiry_date', list_display)
        self.assertEqual(CONTENT_EXPIRY_EXPIRE_FIELD_LABEL, moderation_admin.get_expiry_date.short_description)
