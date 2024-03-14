import datetime
from unittest import skip
from unittest.mock import patch

from django.contrib import admin

from cms.test_utils.testcases import CMSTestCase
from cms.utils.compat import DJANGO_3

from djangocms_versioning.constants import ARCHIVED, DRAFT, PUBLISHED, UNPUBLISHED
from freezegun import freeze_time

from djangocms_content_expiry.admin import ContentExpiryAdmin
from djangocms_content_expiry.filters import ContentTypeFilter
from djangocms_content_expiry.forms import ForeignKeyReadOnlyWidget
from djangocms_content_expiry.models import (
    ContentExpiry,
    DefaultContentExpiryConfiguration,
)
from djangocms_content_expiry.test_utils.factories import (
    DefaultContentExpiryConfigurationFactory,
    UserFactory,
)
from djangocms_content_expiry.test_utils.polls.factories import PollContentExpiryFactory
from djangocms_content_expiry.test_utils.polymorphic_project.factories import (
    ArtProjectContentExpiryFactory,
    ProjectContentExpiryFactory,
    ResearchProjectContentExpiryFactory,
)
from djangocms_content_expiry.test_utils.utils import _get_content_types_set


if DJANGO_3:
    CMSTestCase.assertQuerySetEqual = CMSTestCase.assertQuerysetEqual


class ContentExpiryChangelistExpiryFilterTestCase(CMSTestCase):
    @freeze_time("2200-01-14")
    @patch('djangocms_content_expiry.helpers.DEFAULT_RANGEFILTER_DELTA', 15)
    def test_expired_filter_default_setting(self):
        """
        Default filter is to display all published content on page load
        """
        from_date = datetime.datetime.now()

        # Record that is expired by 1 day
        delta_1 = datetime.timedelta(days=1)
        expire_at_1 = from_date - delta_1
        PollContentExpiryFactory(expires=expire_at_1, version__state=PUBLISHED)

        # Record that is set to expire today
        expire_at_2 = from_date
        poll_content_2 = PollContentExpiryFactory(expires=expire_at_2, version__state=PUBLISHED)

        # Record that is set to expire tomorrow
        delta_3 = datetime.timedelta(days=1)
        expire_at_3 = from_date + delta_3
        poll_content_3 = PollContentExpiryFactory(expires=expire_at_3, version__state=PUBLISHED)

        # Record that is set to expire in 1 day before the end date
        delta_4 = datetime.timedelta(days=14)
        expire_at_4 = from_date + delta_4
        poll_content_4 = PollContentExpiryFactory(expires=expire_at_4, version__state=PUBLISHED)

        # Record that is set to expire the same day as the end date
        delta_5 = datetime.timedelta(days=15)
        expire_at_5 = from_date + delta_5
        poll_content_5 = PollContentExpiryFactory(expires=expire_at_5, version__state=PUBLISHED)

        # Record that is set to expire a day after the end date
        delta_6 = datetime.timedelta(days=16)
        expire_at_6 = from_date + delta_6
        PollContentExpiryFactory(expires=expire_at_6, version__state=PUBLISHED)

        with self.login_user_context(self.get_superuser()):
            admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")
            response = self.client.get(admin_endpoint)

        # Only contents in the date range should be returned
        self.assertQuerySetEqual(
            response.context["cl"].queryset,
            [poll_content_2.version.pk,
             poll_content_3.version.pk,
             poll_content_4.version.pk,
             poll_content_5.version.pk],
            transform=lambda x: x.pk,
            ordered=False,
        )

    @freeze_time("2200-01-14")
    @patch('djangocms_content_expiry.helpers.DEFAULT_RANGEFILTER_DELTA', 15)
    def test_expired_filter_setting_expired_at_range_boundaries(self):
        """
        The boundaries of the Expired by date range filter are
        set to check that only records due to expire are shown with a filter value set at a
        different range to the setting DEFAULT_RANGEFILTER_DELTA. The reason the dates
        need to differ ensure that we not just re-testing the default setting.
        """
        from_date = datetime.datetime.now()
        to_date = from_date + datetime.timedelta(days=110)

        # Record that is expired by 1 day
        delta_1 = datetime.timedelta(days=1)
        expire_at_1 = from_date - delta_1
        PollContentExpiryFactory(expires=expire_at_1, version__state=PUBLISHED)

        # Record that is set to expire today
        expire_at_2 = from_date
        poll_content_2 = PollContentExpiryFactory(expires=expire_at_2, version__state=PUBLISHED)

        # Record that is set to expire tomorrow
        delta_3 = datetime.timedelta(days=1)
        expire_at_3 = from_date + delta_3
        poll_content_3 = PollContentExpiryFactory(expires=expire_at_3, version__state=PUBLISHED)

        # Record that is set to expire in 1 day before the end date
        delta_4 = datetime.timedelta(days=109)
        expire_at_4 = from_date + delta_4
        poll_content_4 = PollContentExpiryFactory(expires=expire_at_4, version__state=PUBLISHED)

        # Record that is set to expire the same day as the end date
        delta_5 = datetime.timedelta(days=110)
        expire_at_5 = from_date + delta_5
        poll_content_5 = PollContentExpiryFactory(expires=expire_at_5, version__state=PUBLISHED)

        # Record that is set to expire a day after the end date
        delta_6 = datetime.timedelta(days=111)
        expire_at_6 = from_date + delta_6
        PollContentExpiryFactory(expires=expire_at_6, version__state=PUBLISHED)

        with self.login_user_context(self.get_superuser()):
            url_date_range = f"?expires__range__gte={from_date.date()}&expires__range__lte={to_date.date()}"
            admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")
            response = self.client.get(admin_endpoint + url_date_range)

        # Only contents in the date range should be returned
        self.assertQuerySetEqual(
            response.context["cl"].queryset,
            [poll_content_2.version.pk,
             poll_content_3.version.pk,
             poll_content_4.version.pk,
             poll_content_5.version.pk],
            transform=lambda x: x.pk,
            ordered=False,
        )

    def test_expired_filter_published_always_filtered(self):
        """
        All published items should never be shown to the user as they have been expired and acted on
        """
        delta = datetime.timedelta(days=31)
        expire = datetime.datetime.now() + delta
        PollContentExpiryFactory(expires=expire, version__state=PUBLISHED)

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(self.get_admin_url(ContentExpiry, "changelist"))

        published_query_set = response.context["cl"].queryset.filter(version__state="published")

        self.assertEqual(len(published_query_set), 0)


class ContentExpiryAuthorFilterTestCase(CMSTestCase):
    def test_author_filter(self):
        """
        Author filter should only show selected author's results
        """
        date = datetime.datetime.now() + datetime.timedelta(days=5)
        # Create records with a set user
        user = UserFactory()
        expiry_author = PollContentExpiryFactory.create_batch(2, expires=date, created_by=user,
                                                              version__state=PUBLISHED)

        # Create records with other random users
        expiry_other_authors = PollContentExpiryFactory.create_batch(4, expires=date, version__state=PUBLISHED)

        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")
        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint)

        # The results should not be filtered
        self.assertQuerySetEqual(
            response.context["cl"].queryset,
            [expiry_author[0].pk, expiry_author[1].pk,
             expiry_other_authors[0].pk, expiry_other_authors[1].pk,
             expiry_other_authors[2].pk, expiry_other_authors[3].pk],
            transform=lambda x: x.pk,
            ordered=False,
        )

        # Filter by a user
        author_selection = f"?created_by={user.pk}"
        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + author_selection)

        # When an author is selected in the filter only the author selected content expiry are shown
        self.assertQuerySetEqual(
            response.context["cl"].queryset,
            [expiry_author[0].pk, expiry_author[1].pk],
            transform=lambda x: x.pk,
            ordered=False,
        )


class ContentExpiryContentTypeFilterTestCase(CMSTestCase):

    def setUp(self):
        self.expiry_date = datetime.datetime.now() + datetime.timedelta(days=5)
        self.poll_expiry = PollContentExpiryFactory(expires=self.expiry_date)
        self.poll_expiry_c_type = self.poll_expiry.version.content_type.pk
        self.project_expiry_set = ProjectContentExpiryFactory.create_batch(2, expires=self.expiry_date)
        self.project_expiry_c_type = self.project_expiry_set[0].version.content.polymorphic_ctype_id
        self.art_expiry_set = ArtProjectContentExpiryFactory.create_batch(2, expires=self.expiry_date)
        self.art_expiry_c_type = self.art_expiry_set[0].version.content.polymorphic_ctype_id
        self.research_expiry_set = ResearchProjectContentExpiryFactory.create_batch(2, expires=self.expiry_date)
        self.research_expiry_c_type = self.research_expiry_set[0].version.content.polymorphic_ctype_id

    def test_content_type_filter_lookup_values(self):
        """
        The lookup values should match the values of versioned content types!
        """
        content_type_filter = ContentTypeFilter(None, {'content_type': ''}, ContentExpiry, ContentExpiryAdmin)
        content_type_list = _get_content_types_set()
        lookup_choices = set(
            ctype[0] for ctype in content_type_filter.lookup_choices
        )

        self.assertSetEqual(lookup_choices, content_type_list)

    def test_content_type_filter_for_simple_models(self):
        content_type = f"?content_type={self.poll_expiry_c_type}&state={DRAFT}"
        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + content_type)

        self.assertQuerySetEqual(
            response.context["cl"].queryset,
            [self.poll_expiry.version.pk],
            transform=lambda x: x.pk,
            ordered=False,
        )

    def test_content_type_filter_for_root_polymorphic_models(self):
        """
        Root polymorphic models should be shown when the model is selected. No other models should be shown,
        especially any concrete models that inherited from the polymorphic model.
        """
        content_type = f"?content_type={self.project_expiry_c_type}&state={DRAFT}"
        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + content_type)

        self.assertQuerySetEqual(
            response.context["cl"].queryset,
            [
                self.project_expiry_set[0].version.pk,
                self.project_expiry_set[1].version.pk,
                self.art_expiry_set[0].version.pk,
                self.art_expiry_set[1].version.pk,
                self.research_expiry_set[0].version.pk,
                self.research_expiry_set[1].version.pk,
            ],
            transform=lambda x: x.pk,
            ordered=False,
        )

    @skip("Polymorphic filtering support is currently not supported due to slow performance")
    def test_content_type_filter_for_concrete_art_polymorphic_models(self):
        """
        Specific concrete models should be shown when the model is selected. No other models should be shown,
        especially any other models that inherit from the polymorphic model.
        """
        content_type = f"?content_type={self.art_expiry_c_type}&state={DRAFT}"
        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + content_type)

        self.assertQuerySetEqual(
            response.context["cl"].queryset,
            [self.art_expiry_set[0].version.pk, self.art_expiry_set[1].version.pk],
            transform=lambda x: x.pk,
            ordered=False,
        )

    @skip("Polymorphic filtering support is currently not supported due to slow performance")
    def test_content_type_filter_for_concrete_research_polymorphic_models(self):
        """
        Specific concrete models should be shown when the model is selected. No other models should be shown,
        especially any other models that inherit from the polymorphic model.
        """
        content_type = f"?content_type={self.research_expiry_c_type}&state={DRAFT}"
        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + content_type)

        self.assertQuerySetEqual(
            response.context["cl"].queryset,
            [self.research_expiry_set[0].version.pk, self.research_expiry_set[1].version.pk],
            transform=lambda x: x.pk,
            ordered=False,
        )

    @skip("Polymorphic filtering support is currently not supported due to slow performance")
    def test_content_type_filter_for_mix_of_concrete_and_root_polymorphic_models(self):
        """
        Specific concrete and root models should be shown when the models are selected.
        No other models should be shown, especially any other models that inherit from the polymorphic model.
        """
        content_type = f"?content_type={self.project_expiry_c_type},{self.art_expiry_c_type}&state={DRAFT}"
        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + content_type)

        self.assertQuerySetEqual(
            response.context["cl"].queryset,
            [
                self.project_expiry_set[0].version.pk,
                self.project_expiry_set[1].version.pk,
                self.art_expiry_set[0].version.pk,
                self.art_expiry_set[1].version.pk,
             ],
            transform=lambda x: x.pk,
            ordered=False,
        )


class ContentExpiryChangelistVersionFilterTestCase(CMSTestCase):
    def test_versions_filters_default(self):
        """
        The default should be to show published versions by default as they are what
        should be expired, we provide the ability to filter the list to find existing entries
        or else there would be no other way to find them.
        """
        date = datetime.datetime.now() + datetime.timedelta(days=5)
        # Create draft records
        PollContentExpiryFactory.create_batch(2, expires=date, version__state=DRAFT)
        # Create published records
        expiry_published_list = PollContentExpiryFactory.create_batch(2, expires=date, version__state=PUBLISHED)
        # Create archived records
        PollContentExpiryFactory.create_batch(2, expires=date, version__state=ARCHIVED)
        # Create unublished records
        PollContentExpiryFactory.create_batch(2, expires=date, version__state=UNPUBLISHED)

        # By default only published entries should exist as that is the default setting
        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint)

        # When an author is selected in the filter only the author selected content expiry are shown
        self.assertQuerySetEqual(
            response.context["cl"].queryset,
            [expiry_published_list[0].pk, expiry_published_list[1].pk],
            transform=lambda x: x.pk,
            ordered=False,
        )

    def test_versions_filters_changing_states(self):
        """
        Filter options can be selected and changed, the expiry records shown should match the
        options selected.
        """
        date = datetime.datetime.now() + datetime.timedelta(days=5)
        # Create draft records
        expiry_draft_list = PollContentExpiryFactory.create_batch(2, expires=date, version__state=DRAFT)
        # Create published records
        expiry_published_list = PollContentExpiryFactory.create_batch(2, expires=date, version__state=PUBLISHED)
        # Create archived records
        expiry_archived_list = PollContentExpiryFactory.create_batch(2, expires=date, version__state=ARCHIVED)
        # Create unublished records
        expiry_unpublished_list = PollContentExpiryFactory.create_batch(2, expires=date, version__state=UNPUBLISHED)

        # When draft is selected only the draft entries should be shown
        version_selection = f"?state={DRAFT}"
        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + version_selection)

        # When an author is selected in the filter only the author selected content expiry are shown
        self.assertQuerySetEqual(
            response.context["cl"].queryset,
            [expiry_draft_list[0].pk, expiry_draft_list[1].pk],
            transform=lambda x: x.pk,
            ordered=False,
        )

        # When published is selected only the draft entries should be shown
        version_selection = f"?state={PUBLISHED}"
        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + version_selection)

        # When an author is selected in the filter only the author selected content expiry are shown
        self.assertQuerySetEqual(
            response.context["cl"].queryset,
            [expiry_published_list[0].pk, expiry_published_list[1].pk],
            transform=lambda x: x.pk,
            ordered=False,
        )

        # When archived is selected only the draft entries should be shown
        version_selection = f"?state={ARCHIVED}"
        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + version_selection)

        # When an author is selected in the filter only the author selected content expiry are shown
        self.assertQuerySetEqual(
            response.context["cl"].queryset,
            [expiry_archived_list[0].pk, expiry_archived_list[1].pk],
            transform=lambda x: x.pk,
            ordered=False,
        )

        # When unpublished is selected only the draft entries should be shown
        version_selection = f"?state={UNPUBLISHED}"
        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + version_selection)

        # When an author is selected in the filter only the author selected content expiry are shown
        self.assertQuerySetEqual(
            response.context["cl"].queryset,
            [expiry_unpublished_list[0].pk, expiry_unpublished_list[1].pk],
            transform=lambda x: x.pk,
            ordered=False,
        )

    def test_versions_filters_multiple_states_selected(self):
        """
        Multiple filters can be selected at once, changing and adding filters
        should show the expiry records based on the multiple options selected
        """
        date = datetime.datetime.now() + datetime.timedelta(days=5)
        # Create draft records
        expiry_draft_list = PollContentExpiryFactory.create_batch(2, expires=date, version__state=DRAFT)
        # Create published records
        expiry_published_list = PollContentExpiryFactory.create_batch(2, expires=date, version__state=PUBLISHED)
        # Create archived records
        expiry_archived_list = PollContentExpiryFactory.create_batch(2, expires=date, version__state=ARCHIVED)
        # Create unublished records
        expiry_unpublished_list = PollContentExpiryFactory.create_batch(2, expires=date, version__state=UNPUBLISHED)

        # Simulate selecting some of the filters
        version_selection = f"?state={ARCHIVED},{UNPUBLISHED}"
        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + version_selection)

        # When an author is selected in the filter only the author selected content expiry are shown
        self.assertQuerySetEqual(
            response.context["cl"].queryset,
            [expiry_archived_list[0].pk, expiry_archived_list[1].pk,
             expiry_unpublished_list[0].pk, expiry_unpublished_list[1].pk, ],
            transform=lambda x: x.pk,
            ordered=False,
        )

        # Simulate selecting all of the filters
        version_selection = f"?state={DRAFT},{PUBLISHED},{ARCHIVED},{UNPUBLISHED}"
        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + version_selection)

        # When an author is selected in the filter only the author selected content expiry are shown
        self.assertQuerySetEqual(
            response.context["cl"].queryset,
            [expiry_draft_list[0].pk, expiry_draft_list[1].pk,
             expiry_published_list[0].pk, expiry_published_list[1].pk,
             expiry_archived_list[0].pk, expiry_archived_list[1].pk,
             expiry_unpublished_list[0].pk, expiry_unpublished_list[1].pk, ],
            transform=lambda x: x.pk,
            ordered=False,
        )

    def test_versions_filters_all_state(self):
        """
        When selecting the All filter option all of the expiry records should be shown,
        selecting another option should remove the all selection.
        """
        date = datetime.datetime.now() + datetime.timedelta(days=5)
        expiry_draft = PollContentExpiryFactory(expires=date, version__state=DRAFT)
        expiry_published = PollContentExpiryFactory(expires=date, version__state=PUBLISHED)
        expiry_archived = PollContentExpiryFactory(expires=date, version__state=ARCHIVED)
        expiry_unpublished = PollContentExpiryFactory(expires=date, version__state=UNPUBLISHED)

        # When draft is selected only the draft entries should be shown
        version_selection = "?state=_all_"
        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + version_selection)

        self.assertQuerySetEqual(
            response.context["cl"].queryset,
            [expiry_draft.pk, expiry_published.pk,
             expiry_archived.pk, expiry_unpublished.pk, ],
            transform=lambda x: x.pk,
            ordered=False,
        )

        # selecting another filter should remove the all option
        version_selection = f"?state={DRAFT}"
        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + version_selection)

        self.assertQuerySetEqual(
            response.context["cl"].queryset,
            [expiry_draft.pk],
            transform=lambda x: x.pk,
            ordered=False,
        )


class ContentExpiryCsvExportFilterSettingsTestCase(CMSTestCase):
    def setUp(self):
        self.date = datetime.datetime.now() + datetime.timedelta(days=5)
        self.admin_endpoint = self.get_admin_url(ContentExpiry, "export_csv")

    def test_version_filter_boundaries_in_export(self):
        """
        Export respects applied version filters.
        CSV data should only export matching versioned state results
        """
        # Create content expiry records for draft and published
        PollContentExpiryFactory(expires=self.date, version__state=DRAFT)
        PollContentExpiryFactory(expires=self.date, version__state=PUBLISHED)

        # When draft is selected only the draft entries should be shown
        version_selection = f"?state={DRAFT}"

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(self.admin_endpoint + version_selection)

        response_content = response.content.decode()

        # Endpoint is returning 200 status code
        self.assertEqual(response.status_code, 200)
        # Only draft content should be exported as the set filter should be respected
        self.assertIn("Draft", response_content)
        # Published content should not be available in exported data if the filter is set to display draft only
        self.assertNotIn('Published', response_content)

    def test_author_filter_boundaries_in_export(self):
        """
        Export respects applied author filters.
        CSV data should only export selected author's results
        """
        version_1 = PollContentExpiryFactory(expires=self.date, version__state=PUBLISHED)
        user_1 = version_1.version.created_by
        version_2 = PollContentExpiryFactory(expires=self.date, version__state=PUBLISHED)
        user_2 = version_2.version.created_by

        # Filter by a user_1
        author_selection = f"?created_by={version_1.pk}"

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(self.admin_endpoint + author_selection)

        response_content = response.content.decode()
        # Endpoint is returning 200 status code
        self.assertEqual(response.status_code, 200)
        # User 1 is in response
        self.assertIn(user_1.username, response_content)
        # User 2 should not be in the response
        self.assertNotIn(user_2.username, response_content)

    def test_content_type_filter_boundaries_in_export(self):
        """
        Export respects applied content type filters.
        CSV data should only export content matching selected content type's results
        """
        content_expiry = PollContentExpiryFactory(expires=self.date, version__state=PUBLISHED)
        version = content_expiry.version

        # Testing page content filter with polls content
        content_type = f"?content_type={version.content_type.pk}"

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(self.admin_endpoint + content_type)

        self.assertContains(response, 'poll content')

    @freeze_time("2200-01-14")
    @patch('djangocms_content_expiry.helpers.DEFAULT_RANGEFILTER_DELTA', 15)
    def test_date_range_filter_boundaries_in_export(self):
        """
        The boundaries of the expired by date range filter are
        set to check that only records due to expire are exported
        """
        from_date = datetime.datetime.now()
        to_date = from_date + datetime.timedelta(days=110)

        # Record that is expired by 1 day
        delta_1 = datetime.timedelta(days=1)
        expire_at_1 = from_date - delta_1
        poll_content_1 = PollContentExpiryFactory(expires=expire_at_1, version__state=PUBLISHED)

        # Record that is set to expire today
        expire_at_2 = from_date
        poll_content_2 = PollContentExpiryFactory(expires=expire_at_2, version__state=PUBLISHED)

        # Record that is set to expire tomorrow
        delta_3 = datetime.timedelta(days=1)
        expire_at_3 = from_date + delta_3
        poll_content_3 = PollContentExpiryFactory(expires=expire_at_3, version__state=PUBLISHED)

        # Record that is set to expire in 1 day before the end date
        delta_4 = datetime.timedelta(days=109)
        expire_at_4 = from_date + delta_4
        poll_content_4 = PollContentExpiryFactory(expires=expire_at_4, version__state=PUBLISHED)

        # Record that is set to expire the same day as the end date
        delta_5 = datetime.timedelta(days=110)
        expire_at_5 = from_date + delta_5
        poll_content_5 = PollContentExpiryFactory(expires=expire_at_5, version__state=PUBLISHED)

        # Record that is set to expire a day after the end date
        delta_6 = datetime.timedelta(days=111)
        expire_at_6 = from_date + delta_6
        poll_content_6 = PollContentExpiryFactory(expires=expire_at_6, version__state=PUBLISHED)

        with self.login_user_context(self.get_superuser()):
            url_date_range = f"?expires__range__gte={from_date.date()}&expires__range__lte={to_date.date()}"
            response = self.client.get(self.admin_endpoint + url_date_range)

        response_content = response.content.decode()

        # Endpoint is returning 200 status code
        self.assertEqual(response.status_code, 200)
        # Content is already expired and should not be included in the export
        self.assertNotIn(poll_content_1.version.content.text, response_content)
        # Content which matches the date range should be exported
        self.assertIn(poll_content_2.version.content.text, response_content)
        self.assertIn(poll_content_3.version.content.text, response_content)
        self.assertIn(poll_content_4.version.content.text, response_content)
        self.assertIn(poll_content_5.version.content.text, response_content)
        # Content that is set to expire a day after the end date should not be exported
        self.assertNotIn(poll_content_6.version.content.text, response_content)


class DefaultContentExpiryConfigurationAdminViewsPermissionsTestCase(CMSTestCase):

    def setUp(self):
        self.model = DefaultContentExpiryConfiguration
        self.content_expiry_configuration = DefaultContentExpiryConfigurationFactory()

    def test_add_permissions(self):
        """
        Adding a default content expiry configuration record via the admin is permitted
        """
        endpoint = self.get_admin_url(self.model, "add")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 200)

    def test_change_permissions(self):
        """
        Changing a default content expiry configuration record via the admin is permitted
        """
        endpoint = self.get_admin_url(self.model, "change",  self.content_expiry_configuration.pk)

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(endpoint, follow=True)

        self.assertEqual(response.status_code, 200)

    def test_delete_permissions(self):
        """
        Deleting a default content expiry configuration record via the admin is permitted
        """
        endpoint = self.get_admin_url(self.model, "delete",  self.content_expiry_configuration.pk)

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(endpoint, follow=True)

        self.assertEqual(response.status_code, 200)


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

        # The list is equal to the content type versionables
        content_type_set = _get_content_types_set()
        content_type_list = list(
            content_type_set
        )

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

        # The list is equal to the content type versionables
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


class ContentExpiryChangelistComplianceNumberFilterTestCase(CMSTestCase):
    def setUp(self):
        self.date = datetime.datetime.now() + datetime.timedelta(days=5)
        self.admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

    def test_compliance_number_filter_boundaries(self):
        """
        Queryset should only contain content matching provided compliance number
        """
        content_expiry_1 = PollContentExpiryFactory(expires=self.date, compliance_number="12345678")
        content_expiry_2 = PollContentExpiryFactory(expires=self.date, compliance_number="91012135")

        compliance_number = f"?compliance_number={content_expiry_1.compliance_number}"

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(self.admin_endpoint + compliance_number)

        response_content = response.content.decode()

        # Endpoint is returning 200 status code
        self.assertEqual(response.status_code, 200)
        # Since we provided the compliance number from content_expiry_1, we expect this to be displayed
        self.assertIn(content_expiry_1.compliance_number, response_content)
        self.assertNotIn(content_expiry_2.compliance_number, response_content)
