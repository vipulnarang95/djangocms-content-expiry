from djangocms_versioning import constants

from djangocms_content_expiry.models import ContentExpiry

from .utils import get_future_expire_date


def create_content_expiry(**kwargs):
    if kwargs['operation'] == constants.OPERATION_DRAFT:
        version = kwargs["obj"]
        # Attempt to find an existing content expiry record from a linked version
        expire_record = ContentExpiry.objects.filter(version_id=version.source_id)
        if not expire_record:
            expiry_date = get_future_expire_date(version, version.created)
        else:
            expiry_date = expire_record[0].expires

        ContentExpiry.objects.create(
            version=version,
            created=version.created,
            created_by=version.created_by,
            expires=expiry_date,
        )
