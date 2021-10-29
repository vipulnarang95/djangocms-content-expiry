import datetime

from django.contrib import admin
from django.utils import timezone

from cms.test_utils.testcases import CMSTestCase

from djangocms_versioning.constants import DRAFT, PUBLISHED

from djangocms_content_expiry.admin import ContentExpiryAdmin
from djangocms_content_expiry.conf import DEFAULT_CONTENT_EXPIRY_EXPORT_DATE_FORMAT
from djangocms_content_expiry.models import ContentExpiry
from djangocms_content_expiry.test_utils.polls.factories import PollContentExpiryFactory


class ContentExpiryAdminViewsPermissionsTestCase(CMSTestCase):
    def setUp(self):
        self.model = ContentExpiry
        self.content_expiry = PollContentExpiryFactory()

    def test_add_permissions(self):
        """
        Adding a content expiry record via the admin is not permitted
        """
        endpoint = self.get_admin_url(self.model, "add")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)

    def test_change_permissions(self):
        """
        Changing a content expiry record via the admin is permitted
        """
        endpoint = self.get_admin_url(self.model, "change",  self.content_expiry.pk)

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 200)

    def test_delete_permissions(self):
        """
        Deleting a content expiry record via the admin is not permitted
        """
        endpoint = self.get_admin_url(self.model, "delete",  self.content_expiry.pk)

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)


class ContentExpiryChangeFormTestCase(CMSTestCase):
    def test_change_form_fields(self):
        """
        Ensure that the form fields present match the model fields
        """
        content_expiry = PollContentExpiryFactory()
        endpoint = self.get_admin_url(ContentExpiry, "change", content_expiry.pk)

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 200)

        decoded_response = response.content.decode("utf-8")

        self.assertIn('name="created_by"', decoded_response)
        self.assertIn('name="version"', decoded_response)
        self.assertIn('name="expires_0"', decoded_response)
        self.assertIn('name="expires_1"', decoded_response)


class ContentExpiryChangelistTestCase(CMSTestCase):
    def setUp(self):
        self.site = admin.AdminSite()
        self.site.register(ContentExpiry, ContentExpiryAdmin)

    def test_change_fields(self):
        """
        Ensure the change list presents list display items from the admin file
        """
        endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(endpoint)

        context = response.context_data['cl'].list_display
        self.assertTrue('title' in context)
        self.assertTrue('content_type' in context)
        self.assertTrue('expires' in context)
        self.assertTrue('version_state' in context)
        self.assertTrue('version_author' in context)

        # Get any computed fields such as the bespoke actions
        list_functions = [field.short_description for field in context if hasattr(field, 'short_description')]

        self.assertTrue('actions' in list_functions)

    def test_preview_link_published_object(self):
        """
        For published objects the live link should be returned
        """
        content_expiry = PollContentExpiryFactory(version__state=PUBLISHED)
        poll_content = content_expiry.version.content

        self.assertEqual(
            self.site._registry[ContentExpiry]._get_preview_url(content_expiry),
            poll_content.get_absolute_url()
        )

    def test_preview_link_draft_object(self):
        """
        For draft / editable objects the preview link should be returned
        """
        content_expiry = PollContentExpiryFactory(version__state=DRAFT)
        poll_content = content_expiry.version.content

        self.assertEqual(
            self.site._registry[ContentExpiry]._get_preview_url(content_expiry),
            poll_content.get_preview_url()
        )


class ContentExpiryCsvExportFileTestCase(CMSTestCase):
    def setUp(self):
        # Use a timezone aware time due to the admin using a timezone
        # which causes a datetime mismatch for the CSV view
        self.date = timezone.now() + datetime.timedelta(days=5)
        # CSV Headings: 0 -> Title, 1 -> Content Type, 2 -> Expiry Date, 3 -> Version State, 4 -> Author, 5 -> Url
        self.headings_map = {
            "title": 0,
            "ctype": 1,
            "expiry_date": 2,
            "version_state": 3,
            "version_author": 4,
            "url": 5,
        }
        self.export_admin_endpoint = self.get_admin_url(ContentExpiry, "export_csv") + "?state=_all_"

    def test_export_button_endpoint_response_is_a_csv(self):
        """
        Valid csv file is returned from the admin export endpoint
        """
        PollContentExpiryFactory(expires=self.date, version__state=DRAFT)

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(self.export_admin_endpoint)

        # Endpoint is returning 200 status code
        self.assertEqual(response.status_code, 200)
        # Response contains a csv file
        self.assertEquals(
            response.get('Content-Disposition'),
            "attachment; filename={}.csv".format("djangocms_content_expiry.contentexpiry")
        )

    def test_export_content_headers(self):
        """
        Export should contain all the headings in the current content expiry list display
        """
        PollContentExpiryFactory(expires=self.date, version__state=DRAFT)

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(self.export_admin_endpoint)

        csv_headings = response.content.decode().splitlines()[0].split(",")

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            csv_headings[self.headings_map["title"]],
            "Title"
        )
        self.assertEqual(
            csv_headings[self.headings_map["ctype"]],
            "Content Type"
        )
        self.assertEqual(
            csv_headings[self.headings_map["expiry_date"]],
            "Expiry Date"
        )
        self.assertEqual(
            csv_headings[self.headings_map["version_state"]],
            "Version State"
        )
        self.assertEqual(
            csv_headings[self.headings_map["version_author"]],
            "Version Author"
        )
        self.assertEqual(
            csv_headings[self.headings_map["url"]],
            "Url"
        )

    def test_file_content_contains_values(self):
        """
        CSV response should contain expected values.

        The dates stored for expiry date are stored with the servers timezone attached, the export
        is exported as UTC so the date time will be converted hence the need to use a timezone aware
        datetime expiry date object.
        """
        content_expiry = PollContentExpiryFactory(expires=self.date, version__state=DRAFT)

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(self.export_admin_endpoint)

        self.assertEqual(response.status_code, 200)

        csv_lines = response.content.decode().splitlines()
        content_row_1 = csv_lines[1].split(",")

        # The following contents should be present
        self.assertEqual(
            content_row_1[self.headings_map["title"]],
            content_expiry.version.content.text
        )
        self.assertEqual(
            content_row_1[self.headings_map["ctype"]],
            content_expiry.version.content_type.name
        )
        self.assertEqual(
            content_row_1[self.headings_map["expiry_date"]],
            content_expiry.expires.strftime(DEFAULT_CONTENT_EXPIRY_EXPORT_DATE_FORMAT)
        )
        self.assertEqual(
            content_row_1[self.headings_map["version_state"]],
            "Draft"
        )
        self.assertEqual(
            content_row_1[self.headings_map["version_author"]],
            content_expiry.version.created_by.username
        )
        self.assertEqual(
            content_row_1[self.headings_map["url"]],
            content_expiry.version.content.get_preview_url()
        )

    def test_export_button_is_visible(self):
        """
        Export button should be visible on the frontend changelist
        """
        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint)

        self.assertContains(
            response,
            '<a class="historylink" href="/en/admin/djangocms_content_expiry/contentexpiry/export_csv/?">Export</a>',
            html=True
        )
