from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from djangocms_versioning.models import Version

from djangocms_content_expiry.models import ContentExpiry
from djangocms_content_expiry.utils import get_future_expire_date


class Command(BaseCommand):
    help = 'Creates Default Content Expiry entries'

    def _populate_existing_version_content_expiry_records(self, forced_expiry_date):
        """
        Create any content expiry records for versions in the system
        """
        for version in Version.objects.filter(contentexpiry__isnull=True):

            self.stdout.write(f"Processing version: {version.pk}")

            # Catch any versions that have no content object attached
            if not version.content:
                self.stdout.write(self.style.WARNING(f"No content found for version: {version.pk}"))
                continue

            # Use a fixed date
            if forced_expiry_date:
                expiry_date = forced_expiry_date
            else:
                # Otherwise: Use the modified date because this is the date that a published
                # version was published which is what really matters for Expired content!
                expiry_date = get_future_expire_date(version, version.modified)

            expiry = ContentExpiry.objects.create(
                created_by=version.created_by,
                version=version,
                expires=expiry_date,
            )

            self.stdout.write(
                f"Content Expiry: {expiry.pk} created for version: {version.pk}"
            )

    def _validate_user_supplied_date(self, expiry_date_string, expiry_date_format):
        """
        Ensure that the date supplied is valid.
        """
        self.stdout.write(
            f"Formatting user supplied date: {expiry_date_string} using the format: {expiry_date_format}"
        )

        try:
            date = datetime.strptime(expiry_date_string, expiry_date_format)
        except ValueError:
            raise CommandError(
                f"This is an incorrect date string: {expiry_date_string} for the format: {expiry_date_format}"
            )

        return date

    def add_arguments(self, parser):
        parser.add_argument(
            '--expiry_date',
            nargs='?',
            help="A fixed date to force all expiry records to use."
        )
        parser.add_argument(
            '--expiry_date_format',
            nargs='?',
            default="%Y-%m-%d",
            help="The format that the expiry_date is provided. "
                 "Uses strptime with the default format: %Y-%m-%d e.g. 2030-03-30"
        )

    def handle(self, *args, **options):
        self.stdout.write(f"Starting {__name__}")

        expiry_date = None
        expiry_date_string = options['expiry_date']
        expiry_date_format = options['expiry_date_format']

        if expiry_date_string:
            expiry_date = self._validate_user_supplied_date(expiry_date_string, expiry_date_format)

        self._populate_existing_version_content_expiry_records(expiry_date)

        self.stdout.write(self.style.SUCCESS(f"Finished {__name__}"))
