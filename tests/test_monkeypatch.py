import datetime

from django.contrib import admin
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.urls import reverse

from cms.test_utils.testcases import CMSTestCase

from djangocms_moderation import constants
from djangocms_versioning.constants import PUBLISHED

from djangocms_content_expiry.constants import CONTENT_EXPIRY_COMPLIANCE_FIELD_LABEL
from djangocms_content_expiry.models import ContentExpiry
from djangocms_content_expiry.test_utils.factories import (
    ChildModerationRequestTreeNodeFactory,
    ModerationCollectionFactory,
    ModerationRequestFactory,
    RootModerationRequestTreeNodeFactory,
    UserFactory,
)
from djangocms_content_expiry.test_utils.polls import factories
from djangocms_content_expiry.test_utils.polls.cms_config import PollsCMSConfig


class ContentExpiryMonkeyPatchTestCase(CMSTestCase):

    def setUp(self):
        from_date = datetime.datetime.now()
        self.user = UserFactory(is_staff=True, is_superuser=True)
        self.client.force_login(self.user)
        self.expires_primary = from_date + datetime.timedelta(days=1)
        self.expires_secondary = from_date + datetime.timedelta(days=2)
        self.content_expiry_primary = factories.PollContentExpiryFactory(
            expires=self.expires_primary,
            version__state=PUBLISHED,
        )
        self.collection = ModerationCollectionFactory(
            author=self.user, status=constants.IN_REVIEW
        )
        self.moderation_request1 = ModerationRequestFactory(
            collection=self.collection,
            version=self.content_expiry_primary.version,
        )
        self.root1 = RootModerationRequestTreeNodeFactory(
            moderation_request=self.moderation_request1
        )

        self.url_pattern = reverse("admin:djangocms_moderation_moderationrequesttreenode_copy")
        self.url = self.url_pattern + "?collection__id={collection_id}&moderation_request__id={mr_id}".format(
            collection_id=self.collection.pk,
            mr_id=self.moderation_request1.pk,
        )
        self.versionable = PollsCMSConfig.versioning[0]

    def test_extended_admin_monkey_patch_list_display_expires(self):
        """
        Monkey patch should add expiry column and values to admin menu list display
        """
        from_date = datetime.datetime.now()

        delta_1 = datetime.timedelta(days=1)
        expire_at_1 = from_date + delta_1
        content_expiry = factories.PollContentExpiryFactory(expires=expire_at_1, version__state=PUBLISHED)
        version_admin = admin.site._registry[content_expiry.version.versionable.version_model_proxy]

        request = RequestFactory().get("/")
        list_display = version_admin.get_list_display(request)

        # List display field should have been added by monkeypatch
        self.assertIn('compliance_number', list_display)
        self.assertEqual(CONTENT_EXPIRY_COMPLIANCE_FIELD_LABEL, version_admin.compliance_number.short_description)

    def test_extended_moderation_admin_update_existing_expiry_record(self):
        """
        If the target of the copy already has an expiry date, the record should be updated, rather than recreated
        """
        # Create db data for additional content expiry!
        self.content_expiry_secondary = factories.PollContentExpiryFactory(
            expires=self.expires_secondary,
            version__state=PUBLISHED
        )
        self.moderation_request2 = ModerationRequestFactory(
            collection=self.collection,
            version=self.content_expiry_secondary.version,
        )
        self.root2 = RootModerationRequestTreeNodeFactory(
            moderation_request=self.moderation_request2
        )
        ChildModerationRequestTreeNodeFactory(
            moderation_request=self.moderation_request1, parent=self.root1
        )

        # Check that expiries are different before we hit the copy endpoint!
        self.assertNotEqual(ContentExpiry.objects.first().expires, ContentExpiry.objects.last().expires)

        response = self.client.post(self.url)

        # Ensure request is a redirect as expected!
        self.assertEqual(response.status_code, 302)
        # Since we already have two content expiry records, we should see an update rather than a creation
        self.assertEqual(ContentExpiry.objects.count(), 2)
        self.assertEqual(ContentExpiry.objects.first().expires, ContentExpiry.objects.last().expires)

    def test_extended_moderation_admin_update_no_expiry_record(self):
        """
        If the user copies a content expiry to a moderation request which does not have an expiry date associated with
        it, one should be created
        """
        # Create db data for additional content expiry!
        ChildModerationRequestTreeNodeFactory(
            moderation_request=self.moderation_request1, parent=self.root1
        )
        poll_content = factories.PollContentWithVersionFactory()
        poll_content.versions.last().contentexpiry.delete()
        self.moderation_request2 = ModerationRequestFactory(
            collection=self.collection,
            version=poll_content.versions.last(),
        )
        self.root2 = RootModerationRequestTreeNodeFactory(
            moderation_request=self.moderation_request2
        )

        # Check that expiries are different before we hit the copy endpoint!
        self.assertEqual(ContentExpiry.objects.count(), 1)

        response = self.client.post(self.url)

        # Ensure request is a redirect as expected!
        self.assertEqual(response.status_code, 302)
        # Since we already have two content expiry records, we should see an update rather than a creation
        self.assertEqual(ContentExpiry.objects.count(), 2)
        self.assertEqual(ContentExpiry.objects.first().expires, ContentExpiry.objects.last().expires)

    def test_extended_moderation_admin_no_redirect_invalid_mr_to_copy(self):
        """
        If the user has tried to copy a content expiry that doesn't exist, nothing should be created!
        """
        ChildModerationRequestTreeNodeFactory(
            moderation_request=self.moderation_request1, parent=self.root1
        )
        poll_content = factories.PollContentWithVersionFactory()
        poll_content.versions.last().contentexpiry.delete()
        self.moderation_request2 = ModerationRequestFactory(
            collection=self.collection,
            version=poll_content.versions.last(),
        )
        self.root2 = RootModerationRequestTreeNodeFactory(
            moderation_request=self.moderation_request2
        )
        self.url = self.url_pattern + "?collection__id={collection_id}&moderation_request__id={mr_id}".format(
            collection_id=self.collection.pk,
            mr_id=self.moderation_request2.pk,
        )

        response = self.client.post(self.url)

        # Only 1 content expiry should be in the database (from the poll content in setUp)
        self.assertEqual(ContentExpiry.objects.count(), 1)
        # We should still be redirected
        self.assertEqual(response.status_code, 302)

    def test_extended_moderation_admin_update_existing_compliance_number_record(self):
        """
        If the target of the copy already has a compliance number, the record should be updated, rather than recreated
        """
        # Create db data for additional content expiry!
        self.content_expiry_secondary = factories.PollContentExpiryFactory(
            expires=self.expires_secondary,
            version__state=PUBLISHED
        )
        self.moderation_request2 = ModerationRequestFactory(
            collection=self.collection,
            version=self.content_expiry_secondary.version,
        )
        self.root2 = RootModerationRequestTreeNodeFactory(
            moderation_request=self.moderation_request2
        )
        ChildModerationRequestTreeNodeFactory(
            moderation_request=self.moderation_request1, parent=self.root1
        )

        # Check that compliance numbers are different before we hit the copy endpoint!
        self.assertEqual(ContentExpiry.objects.count(), 2)
        self.assertNotEqual(ContentExpiry.objects.first().compliance_number,
                            ContentExpiry.objects.last().compliance_number)

        response = self.client.post(self.url + "&copy=compliance")

        # Ensure request is a redirect as expected!
        self.assertEqual(response.status_code, 302)
        # Since we already have two content expiry records, we should see an update rather than a creation
        self.assertEqual(ContentExpiry.objects.count(), 2)
        self.assertEqual(ContentExpiry.objects.first().compliance_number,
                         ContentExpiry.objects.last().compliance_number)

    def test_extended_moderation_admin_update_no_compliance_number_record(self):
        """
        If the user copies a content expiry to a moderation request which does not have a compliance number associated
        with it, one should be not be created as it is not required
        """
        content_expiry = factories.PollContentExpiryFactory(
            expires=self.expires_secondary,
            version__state=PUBLISHED,
            compliance_number="",
        )
        moderation_request = ModerationRequestFactory(
            collection=self.collection,
            version=content_expiry.version,
        )
        RootModerationRequestTreeNodeFactory(
            moderation_request=moderation_request
        )

        # Check that compliance numbers are not set before we hit the copy endpoint!
        content_expiry_record = ContentExpiry.objects.first()
        # Removing the compliance number set in the setup
        content_expiry_record.compliance_number = ""
        # Both records should not contain a compliance number as it has not been set
        self.assertEqual(content_expiry_record.compliance_number, "")
        self.assertEqual(ContentExpiry.objects.last().compliance_number, "")

        response = self.client.post(self.url + "&copy=compliance")

        # Ensure request is a redirect as expected!
        self.assertEqual(response.status_code, 302)
        # The compliance number has not been added so should not be created in the copied versions
        self.assertEqual(ContentExpiry.objects.count(), 2)
        self.assertEqual(ContentExpiry.objects.first().compliance_number,
                         ContentExpiry.objects.last().compliance_number)

    def test_extended_versioning_admin_additional_content_settings_icon(self):
        """
        The additional content settings icon should be added to the version table
        """
        endpoint = self.get_admin_url(ContentExpiry, "change", self.content_expiry_primary.pk)
        additional_settings_control = render_to_string(
            'djangocms_content_expiry/admin/icons/additional_content_settings_icon.html',
            {
                "url": f"{endpoint}?_popup=1"
            }
        )

        querystring = "?poll=1"
        url = self.get_admin_url(self.versionable.version_model_proxy, "changelist") + querystring

        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, additional_settings_control, html=True)
