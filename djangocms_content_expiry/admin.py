from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from .filters import (
    AuthorFilter,
    ContentExpiryDateRangeFilter,
    ContentTypeFilter,
    VersionStateFilter,
)
from .forms import ContentExpiryForm
from .helpers import get_rangefilter_expires_default
from .models import ContentExpiry


@admin.register(ContentExpiry)
class ContentExpiryAdmin(admin.ModelAdmin):
    list_display = ['title', 'content_type', 'expires', 'version_state', 'version_author']
    list_filter = (ContentTypeFilter, ('expires', ContentExpiryDateRangeFilter), VersionStateFilter, AuthorFilter)
    form = ContentExpiryForm

    class Media:
        css = {
            'all': ('djangocms_content_expiry/css/date_filter.css',)
        }

    def has_add_permission(self, *args, **kwargs):
        # Entries are added automatically
        return False

    def has_delete_permission(self, *args, **kwargs):
        # Deletion should never be possible, the only way that a
        # content expiry record could be deleted is via versioning.
        return False

    def get_rangefilter_expires_default(self, *args, **kwargs):
        return get_rangefilter_expires_default()

    def get_rangefilter_expires_title(self, *args, **kwargs):
        return _("By Expiry Date Range")

    def title(self, obj):
        """
        A field to display the content objects title
        """
        return obj.version.content
    title.short_description = _('Title')

    def content_type(self, obj):
        """
        A field to display the content type as a readable representation
        """
        return ContentType.objects.get_for_model(
            obj.version.content
        )
    content_type.short_description = _('Content type')

    def version_state(self, obj):
        """
        A field to display the version state as a readable representation
        """
        return obj.version.get_state_display()
    version_state.short_description = _('Version state')

    def version_author(self, obj):
        """
        A field to display the author of the version
        """
        return obj.version.created_by
    version_author.short_description = _('Version author')
