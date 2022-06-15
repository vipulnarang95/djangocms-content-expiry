import datetime

from django.contrib import admin
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.test import RequestFactory, override_settings
from django.utils import timezone

from cms.api import create_page
from cms.models import PageContent
from cms.test_utils.testcases import CMSTestCase

from bs4 import BeautifulSoup
from djangocms_versioning.constants import DRAFT, PUBLISHED

from djangocms_content_expiry.admin import ContentExpiryAdmin
from djangocms_content_expiry.conf import DEFAULT_CONTENT_EXPIRY_EXPORT_DATE_FORMAT
from djangocms_content_expiry.forms import ForeignKeyReadOnlyWidget
from djangocms_content_expiry.models import (
    ContentExpiry,
    DefaultContentExpiryConfiguration,
)
from djangocms_content_expiry.test_utils.factories import (
    DefaultContentExpiryConfigurationFactory,
)
from djangocms_content_expiry.test_utils.polls.factories import PollContentExpiryFactory
from djangocms_content_expiry.test_utils.polymorphic_project.factories import (
    ArtProjectContentExpiryFactory,
)
from djangocms_content_expiry.test_utils.utils import _get_content_types_set


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

        self.assertIn('compliance_number', decoded_response)
        self.assertIn('name="created_by"', decoded_response)
        self.assertIn('name="version"', decoded_response)
        self.assertIn('name="expires_0"', decoded_response)
        self.assertIn('name="expires_1"', decoded_response)

    def test_change_form_title(self):
        """
        The change form title is populated with the custom value
        """
        content_expiry = PollContentExpiryFactory()
        endpoint = self.get_admin_url(ContentExpiry, "change", content_expiry.pk)

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['title'], 'Additional content settings')


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
            poll_content.get_absolute_url(),
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

    def test_change_icon_tooltip(self):
        """
        The change list presents the correct tooltip when hovering over the change expiry icon
        """
        content_expiry = PollContentExpiryFactory(version__state=DRAFT)
        request = RequestFactory().get("/admin/djangocms_content_expiry/")
        edit_link = self.site._registry[ContentExpiry]._get_edit_link(content_expiry, request)

        soup = BeautifulSoup(str(edit_link), features="lxml")
        actual_link = soup.find("a")
        link_title_tooltip = actual_link.get("title")

        self.assertEqual(
            link_title_tooltip, 'Additional content settings'
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
        art_content_expiry = ArtProjectContentExpiryFactory(expires=self.date, version__state=DRAFT)
        art_preview_url = art_content_expiry.version.content.get_preview_url()
        poll_content_expiry = PollContentExpiryFactory(expires=self.date, version__state=DRAFT)
        poll_preview_url = poll_content_expiry.version.content.get_preview_url()

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(self.export_admin_endpoint)

        self.assertEqual(response.status_code, 200)

        csv_lines = response.content.decode().splitlines()

        # The following contents should be present for poll
        content_row_1 = csv_lines[1].split(",")

        self.assertEqual(
            content_row_1[self.headings_map["title"]],
            poll_content_expiry.version.content.text
        )
        self.assertIn(
            poll_content_expiry.version.content_type.name,
            content_row_1[self.headings_map["ctype"]]
        )
        self.assertEqual(
            content_row_1[self.headings_map["expiry_date"]],
            poll_content_expiry.expires.strftime(DEFAULT_CONTENT_EXPIRY_EXPORT_DATE_FORMAT)
        )
        self.assertEqual(
            content_row_1[self.headings_map["version_state"]],
            "Draft"
        )
        self.assertEqual(
            content_row_1[self.headings_map["version_author"]],
            poll_content_expiry.version.created_by.username
        )
        self.assertNotEqual(
            content_row_1[self.headings_map["url"]],
            poll_preview_url
        )
        self.assertEqual(
            content_row_1[self.headings_map["url"]],
            response.wsgi_request.build_absolute_uri(poll_preview_url)
        )

        # The following contents should be present for art
        content_row_2 = csv_lines[2].split(",")

        self.assertEqual(
            content_row_2[self.headings_map["title"]],
            art_content_expiry.version.content.artist
        )
        self.assertIn(
            art_content_expiry.version.content_type.name,
            content_row_2[self.headings_map["ctype"]]
        )
        self.assertEqual(
            content_row_2[self.headings_map["expiry_date"]],
            art_content_expiry.expires.strftime(DEFAULT_CONTENT_EXPIRY_EXPORT_DATE_FORMAT)
        )
        self.assertEqual(
            content_row_2[self.headings_map["version_state"]],
            "Draft"
        )
        self.assertEqual(
            content_row_2[self.headings_map["version_author"]],
            art_content_expiry.version.created_by.username
        )
        self.assertNotEqual(
            content_row_2[self.headings_map["url"]],
            art_preview_url
        )
        self.assertEqual(
            content_row_2[self.headings_map["url"]],
            response.wsgi_request.build_absolute_uri(art_preview_url)
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


class ContentExpiryChangelistPageContentSiteTestCase(CMSTestCase):

    @classmethod
    def setUpTestData(cls):
        # Site 1
        cls.site_1 = Site.objects.get(id=1)
        # Site 2
        cls.site_2 = Site(id=2, domain='example-2.com', name='example-2.com')
        cls.site_2.save()

    def setUp(self):
        Site.objects.clear_cache()
        # Record that is expired by 1 day
        from_date = datetime.datetime.now()
        expire_at = from_date + datetime.timedelta(days=10)
        language = "en"

        self.superuser = self.get_superuser()
        # Create contents on site 1
        page_1 = create_page(
            title="Site 1 page",
            template="page.html",
            language=language,
            created_by=self.superuser,
            site=self.site_1
        )
        # Publish the site 1 page content
        pagecontent_1 = PageContent._base_manager.filter(page=page_1, language=language).first()
        self.page_1_version = pagecontent_1.versions.first()
        self.page_1_version.publish(self.superuser)

        # Set the expiry date closer than the default
        self.page_1_version.contentexpiry.expires = expire_at
        self.page_1_version.contentexpiry.save()

        # Create contents on site 2
        page_2 = create_page(
            title="Site 2 page",
            template="page.html",
            language=language,
            created_by=self.superuser,
            site=self.site_2
        )
        # Publish the site 2 page content
        pagecontent_2 = PageContent._base_manager.filter(page=page_2, language=language).first()
        self.page_2_version = pagecontent_2.versions.first()
        self.page_2_version.publish(self.superuser)

        # Set the expiry date closer than the default
        self.page_2_version.contentexpiry.expires = expire_at
        self.page_2_version.contentexpiry.save()

    def tearDown(self):
        Site.objects.clear_cache()

    def test_pages_filtered_by_default_site(self):
        """
        The list of change objects must be filtered by the default / current site
        """
        endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(endpoint)

        queryset_result = response.context_data['cl'].result_list

        # Sanity check that the correct site 1 is used
        self.assertEqual(get_current_site(response.request), self.site_1)
        self.assertTrue(len(queryset_result), 1)
        self.assertTrue(queryset_result.first().pk, self.page_1_version.contentexpiry.pk)

    @override_settings(SITE_ID=2)
    def test_pages_filtered_by_other_site(self):
        """
        The list of change objects must be filtered by a different site
        """
        endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(endpoint)

        queryset_result = response.context_data['cl'].result_list

        # Sanity check that the correct site 2 is used
        self.assertEqual(get_current_site(response.request), self.site_2)
        self.assertTrue(len(queryset_result), 1)
        self.assertTrue(queryset_result.first().pk, self.page_2_version.contentexpiry.pk)


class DefaultContentExpiryConfigurationAdminViewsFormsTestCase(CMSTestCase):

    def setUp(self):
        self.model = DefaultContentExpiryConfiguration

    def test_add_form_content_type_items_none_set(self):
        """
        The Content Type list should only show content types that have not yet been created
        and are registered as versioning compatible.
        """
        form = admin.site._registry[DefaultContentExpiryConfiguration].form()
        field_content_type = form.fields['content_type']

        # The list is equal to the content type versionables, get a unique list
        content_type_set = _get_content_types_set()
        content_type_list = list(content_type_set)

        self.assertCountEqual(
            field_content_type.choices.queryset.values_list('id', flat=True),
            content_type_list,
        )

        # Once an entry exists it should no longer be possible to create an entry for it
        poll_content_expiry = PollContentExpiryFactory()
        DefaultContentExpiryConfigurationFactory(
            content_type=poll_content_expiry.version.content_type
        )

        form = admin.site._registry[DefaultContentExpiryConfiguration].form()
        field_content_type = form.fields['content_type']

        # The list is equal to the content type versionables, get a unique list
        content_type_set = _get_content_types_set()
        content_type_list = list(content_type_set)

        # We have to delete the reserved entry because it now exists!
        content_type_list.remove(poll_content_expiry.version.content_type.id)

        self.assertCountEqual(
            field_content_type.choices.queryset.values_list('id', flat=True),
            content_type_list,
        )

    def test_add_form_content_type_submission_not_set(self):
        """
        The Content Type list should still show the content type list if
        the user submitted the form and the content type option was not selected
        """
        poll_content_expiry = PollContentExpiryFactory()
        default_expiry_configuration = DefaultContentExpiryConfigurationFactory(
            content_type=poll_content_expiry.version.content_type
        )
        preload_form_data = {
            "id": default_expiry_configuration.pk,
            "duration": default_expiry_configuration.duration,
        }
        form = admin.site._registry[DefaultContentExpiryConfiguration].form(preload_form_data)
        field_content_type = form.fields['content_type']

        self.assertNotEqual(field_content_type.widget.__class__, ForeignKeyReadOnlyWidget)

    def test_change_form_content_type_items(self):
        """
        The Content Type control should be read only and not allow the user to change it
        """
        poll_content_expiry = PollContentExpiryFactory()
        default_expiry_configuration = DefaultContentExpiryConfigurationFactory(
            content_type=poll_content_expiry.version.content_type
        )
        form = admin.site._registry[DefaultContentExpiryConfiguration].form(instance=default_expiry_configuration)
        field_content_type = form.fields['content_type']

        self.assertEqual(field_content_type.widget.__class__, ForeignKeyReadOnlyWidget)
