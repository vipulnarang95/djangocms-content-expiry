from cms.test_utils.testcases import CMSTestCase

import datetime
from djangocms_versioning.constants import ARCHIVED, DRAFT, PUBLISHED, UNPUBLISHED

from djangocms_content_expiry.models import ContentExpiry
from djangocms_content_expiry.test_utils.factories import UserFactory
from djangocms_content_expiry.test_utils.polls.factories import PollContentExpiryFactory


class ContentExpiryChangelistTestCase(CMSTestCase):
    def test_changelist_form_fields(self):
        """
        Ensure that the form fields present match the model fields"
        """
        with self.login_user_context(self.get_superuser()):
            response = self.client.get(self.get_admin_url(ContentExpiry, "add"))

        self.assertEqual(response.status_code, 200)

        decoded_response = response.content.decode("utf-8")

        self.assertIn('<select name="created_by" required id="id_created_by">', decoded_response)
        self.assertIn('<select name="version" required id="id_version">', decoded_response)
        self.assertIn('<input type="text" name="expires_0" class="vDateField" size="10" required id="id_expires_0">',
                      decoded_response)

    def test_change_fields(self):
        """
        Ensure the change list presents list display items from the admin file
        """
        with self.login_user_context(self.get_superuser()):
            response = self.client.get(self.get_admin_url(ContentExpiry, "changelist"))

        context = response.context_data['cl'].list_display
        self.assertEqual('title', context[1])
        self.assertEqual('content_type', context[2])
        self.assertEqual('expires', context[3])
        self.assertEqual('version_state', context[4])
        self.assertEqual('version_author', context[5])


class ContentExpiryChangelistExpiryFilterTestCase(CMSTestCase):
    def test_expired_filter_default_setting(self):
        """
        Default filter is to display all published content on page load
        """
        from_date = datetime.datetime.now()

        # Record that is expired by 1 day
        delta_1 = datetime.timedelta(days=1)
        expire_at_1 = from_date + delta_1
        PollContentExpiryFactory(expires=expire_at_1, version__state=PUBLISHED)

        # Record that is set to expire today
        expire_at_2 = from_date
        poll_content_2 = PollContentExpiryFactory(expires=expire_at_2, version__state=PUBLISHED)
        version_2 = poll_content_2.version

        # Record that is set to expire tomorrow
        delta_3 = datetime.timedelta(days=1)
        expire_at_3 = from_date - delta_3
        poll_content_3 = PollContentExpiryFactory(expires=expire_at_3, version__state=PUBLISHED)
        version_3 = poll_content_3.version

        # Record that is set to expire in 29 days
        delta_4 = datetime.timedelta(days=29)
        expire_at_4 = from_date - delta_4
        poll_content_4 = PollContentExpiryFactory(expires=expire_at_4, version__state=PUBLISHED)
        version_4 = poll_content_4.version

        # Record that is set to expire in 30 days
        delta_5 = datetime.timedelta(days=30)
        expire_at_5 = from_date - delta_5
        poll_content_5 = PollContentExpiryFactory(expires=expire_at_5, version__state=PUBLISHED)
        poll_content_5.version

        # Record that is set to expire in 31 days
        delta_6 = datetime.timedelta(days=31)
        expire_at_6 = from_date + delta_6
        PollContentExpiryFactory(expires=expire_at_6, version__state=PUBLISHED)

        with self.login_user_context(self.get_superuser()):
            admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")
            response = self.client.get(admin_endpoint)

        # Only contents in the 30 date range should be returned
        self.assertQuerysetEqual(
            response.context["cl"].queryset,
            [version_2.pk, version_3.pk,
             version_4.pk],
            transform=lambda x: x.pk,
            ordered=False,
        )

    def test_expired_filter_setting_expired_at_range_boundaries(self):
        """
        Check the boundaries of the Expired by date range filter. The dates are
        set to check that only records due to expire are shown with a filter value set at 30 days
        """
        from_date = datetime.datetime.now()
        to_date = from_date - datetime.timedelta(days=30)

        # Record that is expired by 1 day
        delta_1 = datetime.timedelta(days=1)
        expire_at_1 = from_date + delta_1
        PollContentExpiryFactory(expires=expire_at_1, version__state=PUBLISHED)

        # Record that is set to expire today
        expire_at_2 = from_date
        poll_content_2 = PollContentExpiryFactory(expires=expire_at_2, version__state=PUBLISHED)
        version_2 = poll_content_2.version

        # Record that is set to expire tomorrow
        delta_3 = datetime.timedelta(days=1)
        expire_at_3 = from_date - delta_3
        poll_content_3 = PollContentExpiryFactory(expires=expire_at_3, version__state=PUBLISHED)
        version_3 = poll_content_3.version

        # Record that is set to expire in 29 days
        delta_4 = datetime.timedelta(days=29)
        expire_at_4 = from_date - delta_4
        poll_content_4 = PollContentExpiryFactory(expires=expire_at_4, version__state=PUBLISHED)
        version_4 = poll_content_4.version

        # Record that is set to expire in 30 days
        delta_5 = datetime.timedelta(days=30)
        expire_at_5 = from_date - delta_5
        PollContentExpiryFactory(expires=expire_at_5, version__state=PUBLISHED)

        # Record that is set to expire in 31 days
        delta_6 = datetime.timedelta(days=31)
        expire_at_6 = from_date - delta_6
        PollContentExpiryFactory(expires=expire_at_6, version__state=PUBLISHED)

        with self.login_user_context(self.get_superuser()):
            url_date_range = f"?expires__range__gte={to_date.date()}&expires__range__lte={from_date.date()}"
            admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")
            response = self.client.get(admin_endpoint + url_date_range)
        # content_expiry_1, content_expiry_5, content_expiry_6 are not shown because they are outside of the set
        # boundary range, content_expiry_1 is before the start and content_expiry_5 and content_expiry_6 is
        # outside of the range.
        self.assertQuerysetEqual(
            response.context["cl"].queryset,
            [version_2.pk, version_3.pk,
             version_4.pk],
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
        date = datetime.datetime.now() - datetime.timedelta(days=5)
        # Create records with a set user
        user = UserFactory()
        expiry_author = PollContentExpiryFactory.create_batch(2, expires=date, created_by=user,
                                                              version__state=PUBLISHED)

        # Create records with other random users
        expiry_other_authors = PollContentExpiryFactory.create_batch(4, expires=date, version__state=PUBLISHED)

        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")
        # url_all = f"?state=_all_"
        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint)

        # The results should not be filtered
        self.assertQuerysetEqual(
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
        self.assertQuerysetEqual(
            response.context["cl"].queryset,
            [expiry_author[0].pk, expiry_author[1].pk],
            transform=lambda x: x.pk,
            ordered=False,
        )


class ContentExpiryContentTypeFilterTestCase(CMSTestCase):
    def test_content_type_filter(self):
        """
        Content type filter should only show relevant content type when filter is selected
        """
        date = datetime.datetime.now() - datetime.timedelta(days=5)

        poll_content_expiry = PollContentExpiryFactory(expires=date)
        version = poll_content_expiry.version

        # Testing page content filter with polls content
        content_type = f"?content_type={version.content_type.pk}&state={DRAFT}"

        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + content_type)

        self.assertQuerysetEqual(
            response.context["cl"].queryset,
            [version.pk],
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
        date = datetime.datetime.now() - datetime.timedelta(days=5)
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
        self.assertQuerysetEqual(
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
        date = datetime.datetime.now() - datetime.timedelta(days=5)
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
        self.assertQuerysetEqual(
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
        self.assertQuerysetEqual(
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
        self.assertQuerysetEqual(
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
        self.assertQuerysetEqual(
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
        date = datetime.datetime.now() - datetime.timedelta(days=5)
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
        self.assertQuerysetEqual(
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
        self.assertQuerysetEqual(
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
        date = datetime.datetime.now() - datetime.timedelta(days=5)
        expiry_draft = PollContentExpiryFactory(expires=date, version__state=DRAFT)
        expiry_published = PollContentExpiryFactory(expires=date, version__state=PUBLISHED)
        expiry_archived = PollContentExpiryFactory(expires=date, version__state=ARCHIVED)
        expiry_unpublished = PollContentExpiryFactory(expires=date, version__state=UNPUBLISHED)

        # When draft is selected only the draft entries should be shown
        version_selection = "?state=_all_"
        admin_endpoint = self.get_admin_url(ContentExpiry, "changelist")

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + version_selection)

        self.assertQuerysetEqual(
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

        self.assertQuerysetEqual(
            response.context["cl"].queryset,
            [expiry_draft.pk],
            transform=lambda x: x.pk,
            ordered=False,
        )
