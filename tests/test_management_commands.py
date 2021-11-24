from datetime import datetime
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from cms.test_utils.testcases import CMSTestCase

import factory
from djangocms_versioning.models import Version
from djangocms_versioning.signals import post_version_operation, pre_version_operation

from djangocms_content_expiry.test_utils.polls.factories import PollVersionFactory
from djangocms_content_expiry.test_utils.polymorphic_project.factories import (
    ProjectContentVersionFactory,
)
from djangocms_content_expiry.utils import get_default_duration_for_version


class CreateExpiryRecordsDefaultLogicTestCase(TestCase):

    def setUp(self):
        self.out = StringIO()

    def test_basic_command_output(self):
        """
        The command should provide messages to the user when starting and when it is finished,
        """
        call_command("create_existing_versions_expiry_records", stdout=self.out)

        self.assertIn(
            "Starting djangocms_content_expiry.management.commands.create_existing_versions_expiry_records",
            self.out.getvalue()
        )
        self.assertIn(
            "Finished djangocms_content_expiry.management.commands.create_existing_versions_expiry_records",
            self.out.getvalue()
        )

    @factory.django.mute_signals(pre_version_operation, post_version_operation)
    def test_default_logic(self):
        """
        By default all expiry records will use a default expiry date
        """
        poll_content_versions = PollVersionFactory.create_batch(5, content__language="en")
        project_content_versions = ProjectContentVersionFactory.create_batch(5)

        # A sanity check to ensure that the models don't have expiry records attached
        # because we are adding them in the command!
        self.assertFalse(hasattr(poll_content_versions[0], "contentexpiry"))
        self.assertFalse(hasattr(project_content_versions[0], "contentexpiry"))

        call_command(
            "create_existing_versions_expiry_records",
            stdout=self.out,
        )

        versions = Version.objects.all()

        self.assertEqual(len(versions), 10)

        for version in versions:
            expected_date = version.modified + get_default_duration_for_version(version)

            self.assertEqual(version.contentexpiry.expires, expected_date)


class CreateExpiryRecordsDateOverrideLogicTestCase(CMSTestCase):

    def setUp(self):
        self.out = StringIO()

    def test_date_options_valid_date_default_format(self):
        """
        When a valid date string is supplied an informative message is supplied
        stating that it is valid
        """
        date = "2100-02-22"

        call_command(
            "create_existing_versions_expiry_records",
            expiry_date=date,
            stdout=self.out,
        )

        self.assertIn(
            f"Formatting user supplied date: {date} using the format: %Y-%m-%d",
            self.out.getvalue()
        )

    def test_date_options_invalid_date_default_format(self):
        """
        When a date string is supplied that doesn't match the default format string an
        informative error message should be shown to the user
        """
        date = "210-02-22"

        with self.assertRaisesMessage(
            CommandError,
            f"This is an incorrect date string: {date} for the format: %Y-%m-%d"
        ):

            call_command(
                "create_existing_versions_expiry_records",
                expiry_date=date,
                stdout=self.out,
            )

    def test_date_options_valid_date_supplied_format(self):
        """
        When a valid date string is supplied an informative message is supplied
        stating that it is valid
        """
        date = "22022100"
        date_format = "%d%m%Y"

        call_command(
            "create_existing_versions_expiry_records",
            expiry_date=date,
            expiry_date_format=date_format,
            stdout=self.out,
        )

        self.assertIn(
            f"Formatting user supplied date: {date} using the format: {date_format}",
            self.out.getvalue()
        )

    def test_date_options_invalid_date_supplied_format(self):
        """
        When a date string is supplied that doesn't match the default format string an
        informative error message should be shown to the user
        """
        date = "210-02-22"
        date_format = "%d%m%Y"

        with self.assertRaisesMessage(
            CommandError,
            f"This is an incorrect date string: {date} for the format: {date_format}"
        ):

            call_command(
                "create_existing_versions_expiry_records",
                expiry_date=date,
                expiry_date_format=date_format,
                stdout=self.out,
            )

    @factory.django.mute_signals(pre_version_operation, post_version_operation)
    def test_date_supplied_import_logic(self):
        """
        When a date is supplied to the command all content expiry records
        should expire on that exact date and time
        """
        date = "2100-02-22"
        date_format = "%Y-%m-%d"
        poll_content_versions = PollVersionFactory.create_batch(5, content__language="en")
        project_content_versions = ProjectContentVersionFactory.create_batch(5)

        # A sanity check to ensure that the models don't have expiry records attached
        # because we are adding them in the command!
        self.assertFalse(hasattr(poll_content_versions[0], "contentexpiry"))
        self.assertFalse(hasattr(project_content_versions[0], "contentexpiry"))

        call_command(
            "create_existing_versions_expiry_records",
            expiry_date=date,
            expiry_date_format=date_format,
            stdout=self.out,
        )

        versions = Version.objects.all()

        self.assertEqual(len(versions), 10)

        for version in versions:
            expected_date = datetime.strptime(date, date_format)
            expected_date = timezone.make_aware(expected_date)

            self.assertEqual(version.contentexpiry.expires, expected_date)
