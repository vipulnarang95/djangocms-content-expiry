from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

import datetime
from rangefilter.filters import DateRangeFilter

from .filters import AuthorFilter, ContentTypeFilter, VersionStateFilter
from .models import ContentExpiry


@admin.register(ContentExpiry)
class ContentExpiryAdmin(admin.ModelAdmin):
    list_display = ['title', 'content_type', 'expires', 'version_state', 'version_author']
    # Disable automatically linking to the Expiry record
    list_display_links = None
    list_filter = (ContentTypeFilter, ('expires', DateRangeFilter), VersionStateFilter, AuthorFilter)

    class Media:
        css = {
            'all': ('css/date_filter.css',)
        }

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        if 'expires__range' not in request.path:
            default_gte, default_lte = self.get_rangefilter_expires_default(request)
            queryset = queryset.filter(expires__range=(default_gte, default_lte))
        return queryset

    def get_rangefilter_expires_default(self, request):
        start_date = datetime.datetime.now() - datetime.timedelta(30)
        end_date = datetime.datetime.now()
        return start_date, end_date

    def get_rangefilter_expires_title(self, request, field_path):
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
